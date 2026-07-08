import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: 'openapi.json',
  output: 'src/client',
  plugins: [
    { name: '@hey-api/client-fetch', runtimeConfigPath: './src/lib/api' },
    '@tanstack/react-query',
  ],
})
