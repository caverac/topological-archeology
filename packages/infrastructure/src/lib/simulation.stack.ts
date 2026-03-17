import fs = require('fs')
import path = require('path')

import * as cdk from 'aws-cdk-lib'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources'
import * as logs from 'aws-cdk-lib/aws-logs'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as sqs from 'aws-cdk-lib/aws-sqs'
import { Construct } from 'constructs'
import { DeploymentEnvironment } from 'utils/types'

export interface SimulationStackProps extends cdk.StackProps {
  deploymentEnvironment: DeploymentEnvironment
  bucket: s3.IBucket
}

export class SimulationStack extends cdk.Stack {
  public readonly queue: sqs.Queue

  constructor(scope: Construct, id: string, props: SimulationStackProps) {
    super(scope, id, props)

    const deadLetterQueue = new sqs.Queue(this, 'DeadLetterQueue', {
      queueName: 'topo-archeo-dead-letter',
      retentionPeriod: cdk.Duration.days(14)
    })

    this.queue = new sqs.Queue(this, 'SimulationQueue', {
      queueName: 'topo-archeo-simulations',
      visibilityTimeout: cdk.Duration.minutes(6),
      retentionPeriod: cdk.Duration.days(14),
      deadLetterQueue: {
        queue: deadLetterQueue,
        maxReceiveCount: 3
      }
    })

    const workerLogGroup = new logs.LogGroup(this, 'WorkerLogGroup', {
      logGroupName: '/aws/lambda/topo_archeo__worker',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    })

    // Copy disk-evolution source into the Docker context so it can be
    // pip-installed inside the container for the target architecture.
    const workerDir = path.join(__dirname, '..', '..', 'lambda', 'worker')
    const diskEvolutionDir = path.resolve(workerDir, '..', '..', '..', 'disk-evolution')
    const vendorDir = path.join(workerDir, 'disk-evolution-src')

    fs.mkdirSync(vendorDir, { recursive: true })
    for (const name of ['pyproject.toml', 'src']) {
      fs.cpSync(path.join(diskEvolutionDir, name), path.join(vendorDir, name), {
        recursive: true,
        force: true
      })
    }

    const workerFn = new lambda.DockerImageFunction(this, 'WorkerFn', {
      functionName: 'topo_archeo__worker',
      code: lambda.DockerImageCode.fromImageAsset('lambda/worker'),
      architecture: lambda.Architecture.ARM_64,
      memorySize: 512,
      timeout: cdk.Duration.minutes(5),
      logGroup: workerLogGroup,
      environment: {
        BUCKET_NAME: props.bucket.bucketName
      }
    })

    workerFn.addEventSource(
      new lambdaEventSources.SqsEventSource(this.queue, {
        batchSize: 1,
        maxConcurrency: 500
      })
    )

    props.bucket.grantReadWrite(workerFn)
  }
}
