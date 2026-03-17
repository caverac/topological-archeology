import { DeploymentEnvironmentSchema, EnvironmentVariablesSchema } from 'utils/types'

describe('types', () => {
  test('DeploymentEnvironmentSchema accepts valid values', () => {
    expect(DeploymentEnvironmentSchema.parse('development')).toBe('development')
    expect(DeploymentEnvironmentSchema.parse('staging')).toBe('staging')
    expect(DeploymentEnvironmentSchema.parse('production')).toBe('production')
  })

  test('DeploymentEnvironmentSchema rejects invalid values', () => {
    expect(() => DeploymentEnvironmentSchema.parse('invalid')).toThrow()
  })

  test('EnvironmentVariablesSchema validates ENVIRONMENT', () => {
    const result = EnvironmentVariablesSchema.parse({ ENVIRONMENT: 'development' })
    expect(result.ENVIRONMENT).toBe('development')
  })

  test('EnvironmentVariablesSchema rejects missing ENVIRONMENT', () => {
    expect(() => EnvironmentVariablesSchema.parse({})).toThrow()
  })
})
