import { Match } from 'aws-cdk-lib/assertions'

import { createGitHubOIDCTemplate } from './helpers'

describe('GitHubOIDCStack', () => {
  test('creates an IAM role for GitHub Actions', () => {
    const template = createGitHubOIDCTemplate()
    template.hasResourceProperties('AWS::IAM::Role', {
      RoleName: 'TopoArcheo-GitHubActions-Role',
      MaxSessionDuration: 3600
    })
  })

  test('role trusts GitHub OIDC provider', () => {
    const template = createGitHubOIDCTemplate()
    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: 'sts:AssumeRoleWithWebIdentity',
            Condition: Match.objectLike({
              StringEquals: {
                'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
              }
            })
          })
        ])
      }
    })
  })

  test('creates SSM parameter with role ARN', () => {
    const template = createGitHubOIDCTemplate()
    template.hasResourceProperties('AWS::SSM::Parameter', {
      Name: '/topo-archeo/github-actions/role-arn'
    })
  })

  test('creates OIDC provider when no existing ARN provided', () => {
    const template = createGitHubOIDCTemplate(
      'caverac/topological-archeology',
      undefined,
      undefined
    )
    template.resourceCountIs('Custom::AWSCDKOpenIdConnectProvider', 1)
  })

  test('reuses existing provider when ARN provided', () => {
    const template = createGitHubOIDCTemplate(
      'caverac/topological-archeology',
      undefined,
      'arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com'
    )
    template.resourceCountIs('Custom::AWSCDKOpenIdConnectProvider', 0)
  })

  test('defaults to development and production environments', () => {
    const template = createGitHubOIDCTemplate()
    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Condition: Match.objectLike({
              StringLike: {
                'token.actions.githubusercontent.com:sub': Match.arrayWith([
                  'repo:caverac/topological-archeology:environment:development',
                  'repo:caverac/topological-archeology:environment:production'
                ])
              }
            })
          })
        ])
      }
    })
  })

  test('restricts to specified environments', () => {
    const template = createGitHubOIDCTemplate('caverac/topological-archeology', ['production'])
    template.hasResourceProperties('AWS::IAM::Role', {
      AssumeRolePolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Condition: Match.objectLike({
              StringLike: {
                'token.actions.githubusercontent.com:sub': [
                  'repo:caverac/topological-archeology:environment:production'
                ]
              }
            })
          })
        ])
      }
    })
  })
})
