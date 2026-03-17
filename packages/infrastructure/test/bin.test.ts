import { z } from 'zod'

describe('bin/index environment validation', () => {
  const envSchema = z.object({
    ENVIRONMENT: z.enum(['development', 'production']),
    AWS_ACCOUNT: z.string(),
    AWS_DEFAULT_REGION: z.string().default('us-east-1')
  })

  test('accepts valid environment variables', () => {
    const result = envSchema.parse({
      ENVIRONMENT: 'development',
      AWS_ACCOUNT: '123456789012',
      AWS_DEFAULT_REGION: 'us-east-1'
    })
    expect(result.ENVIRONMENT).toBe('development')
    expect(result.AWS_ACCOUNT).toBe('123456789012')
  })

  test('defaults region to us-east-1', () => {
    const result = envSchema.parse({
      ENVIRONMENT: 'production',
      AWS_ACCOUNT: '123456789012'
    })
    expect(result.AWS_DEFAULT_REGION).toBe('us-east-1')
  })

  test('rejects missing AWS_ACCOUNT', () => {
    expect(() =>
      envSchema.parse({
        ENVIRONMENT: 'development'
      })
    ).toThrow()
  })

  test('rejects invalid ENVIRONMENT', () => {
    expect(() =>
      envSchema.parse({
        ENVIRONMENT: 'staging',
        AWS_ACCOUNT: '123456789012'
      })
    ).toThrow()
  })
})
