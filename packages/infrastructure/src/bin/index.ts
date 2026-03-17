import * as cdk from 'aws-cdk-lib'
import { DataLakeStack } from 'lib/data-lake.stack'
import { GitHubOIDCStack } from 'lib/github-oidc.stack'
import { SimulationStack } from 'lib/simulation.stack'
import { z } from 'zod'

const envSchema = z.object({
  ENVIRONMENT: z.enum(['development', 'production']),
  AWS_ACCOUNT: z.string(),
  AWS_DEFAULT_REGION: z.string().default('us-east-1')
})

const env = envSchema.parse(process.env)

const cdkEnv = {
  account: env.AWS_ACCOUNT,
  region: env.AWS_DEFAULT_REGION
}

const app = new cdk.App()

const dataLake = new DataLakeStack(app, 'TADataLake', {
  deploymentEnvironment: env.ENVIRONMENT,
  env: cdkEnv
})

new SimulationStack(app, 'TASimulation', {
  deploymentEnvironment: env.ENVIRONMENT,
  bucket: dataLake.bucket,
  env: cdkEnv
})

new GitHubOIDCStack(app, 'TAGitHubOIDC', {
  githubRepo: 'caverac/topological-archeology',
  existingProviderArn: `arn:aws:iam::${env.AWS_ACCOUNT}:oidc-provider/token.actions.githubusercontent.com`,
  env: cdkEnv
})
