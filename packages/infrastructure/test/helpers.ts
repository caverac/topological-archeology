import * as cdk from 'aws-cdk-lib'
import { Template } from 'aws-cdk-lib/assertions'
import { DataLakeStack } from 'lib/data-lake.stack'
import { GitHubOIDCStack } from 'lib/github-oidc.stack'
import { SimulationStack } from 'lib/simulation.stack'
import { DeploymentEnvironment } from 'utils/types'

export function createDataLakeTemplate(
  environment: DeploymentEnvironment = 'development'
): Template {
  const app = new cdk.App()
  const stack = new DataLakeStack(app, 'TestDataLake', {
    deploymentEnvironment: environment,
    env: { account: '123456789012', region: 'us-east-1' }
  })
  return Template.fromStack(stack)
}

export function createSimulationTemplate(
  environment: DeploymentEnvironment = 'development'
): Template {
  const app = new cdk.App()
  const dataLake = new DataLakeStack(app, 'TestDataLake', {
    deploymentEnvironment: environment,
    env: { account: '123456789012', region: 'us-east-1' }
  })
  const stack = new SimulationStack(app, 'TestSimulation', {
    deploymentEnvironment: environment,
    bucket: dataLake.bucket,
    env: { account: '123456789012', region: 'us-east-1' }
  })
  return Template.fromStack(stack)
}

export function createGitHubOIDCTemplate(
  githubRepo = 'caverac/topological-archeology',
  allowedEnvironments?: DeploymentEnvironment[],
  existingProviderArn?: string
): Template {
  const app = new cdk.App()
  const stack = new GitHubOIDCStack(app, 'TestGitHubOIDC', {
    githubRepo,
    allowedEnvironments,
    existingProviderArn,
    env: { account: '123456789012', region: 'us-east-1' }
  })
  return Template.fromStack(stack)
}
