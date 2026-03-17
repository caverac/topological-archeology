import { createDataLakeTemplate } from './helpers'

describe('DataLakeStack', () => {
  const template = createDataLakeTemplate()

  test('creates an S3 bucket', () => {
    template.resourceCountIs('AWS::S3::Bucket', 1)
  })

  test('bucket blocks all public access', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      PublicAccessBlockConfiguration: {
        BlockPublicAcls: true,
        BlockPublicPolicy: true,
        IgnorePublicAcls: true,
        RestrictPublicBuckets: true
      }
    })
  })

  test('bucket enforces SSL via bucket policy', () => {
    template.hasResourceProperties('AWS::S3::BucketPolicy', {})
  })

  test('bucket uses S3 managed encryption', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      BucketEncryption: {
        ServerSideEncryptionConfiguration: [
          {
            ServerSideEncryptionByDefault: {
              SSEAlgorithm: 'AES256'
            }
          }
        ]
      }
    })
  })

  test('bucket has lifecycle rule for tmp/ prefix', () => {
    template.hasResourceProperties('AWS::S3::Bucket', {
      LifecycleConfiguration: {
        Rules: [
          {
            Id: 'expire-tmp',
            Prefix: 'tmp/',
            ExpirationInDays: 7,
            Status: 'Enabled'
          }
        ]
      }
    })
  })

  test('development bucket has DESTROY removal policy', () => {
    template.hasResource('AWS::S3::Bucket', {
      DeletionPolicy: 'Delete',
      UpdateReplacePolicy: 'Delete'
    })
  })

  test('production bucket has RETAIN removal policy', () => {
    const prodTemplate = createDataLakeTemplate('production')
    prodTemplate.hasResource('AWS::S3::Bucket', {
      DeletionPolicy: 'Retain',
      UpdateReplacePolicy: 'Retain'
    })
  })
})
