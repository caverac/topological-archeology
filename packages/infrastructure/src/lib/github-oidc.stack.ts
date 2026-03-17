import * as cdk from 'aws-cdk-lib'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as ssm from 'aws-cdk-lib/aws-ssm'
import { Construct } from 'constructs'
import { DeploymentEnvironment } from 'utils/types'

export interface GitHubOIDCStackProps extends cdk.StackProps {
  githubRepo: string
  allowedEnvironments?: DeploymentEnvironment[]
  existingProviderArn?: string
}

export class GitHubOIDCStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: GitHubOIDCStackProps) {
    super(scope, id, props)

    const provider = props.existingProviderArn
      ? iam.OpenIdConnectProvider.fromOpenIdConnectProviderArn(
          this,
          'GitHubProvider',
          props.existingProviderArn
        )
      : new iam.OpenIdConnectProvider(this, 'GitHubProvider', {
          url: 'https://token.actions.githubusercontent.com',
          clientIds: ['sts.amazonaws.com'],
          thumbprints: [
            '6938fd4d98bab03faadb97b34396831e3780aea1',
            '1c58a3a8518e8759bf075b76b750d4f2df264fcd'
          ]
        })

    const environments = props.allowedEnvironments ?? ['development', 'production']
    const conditions: string[] = environments.map(
      (env) => `repo:${props.githubRepo}:environment:${env}`
    )

    const role = new iam.Role(this, 'GitHubActionsRole', {
      roleName: 'TopoArcheo-GitHubActions-Role',
      maxSessionDuration: cdk.Duration.hours(1),
      assumedBy: new iam.FederatedPrincipal(
        provider.openIdConnectProviderArn,
        {
          StringEquals: {
            'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
          },
          StringLike: {
            'token.actions.githubusercontent.com:sub': conditions
          }
        },
        'sts:AssumeRoleWithWebIdentity'
      )
    })

    role.addToPolicy(
      new iam.PolicyStatement({
        actions: ['sts:AssumeRole'],
        resources: ['arn:aws:iam::*:role/cdk-*']
      })
    )

    new ssm.StringParameter(this, 'RoleArnParameter', {
      parameterName: '/topo-archeo/github-actions/role-arn',
      stringValue: role.roleArn
    })
  }
}
