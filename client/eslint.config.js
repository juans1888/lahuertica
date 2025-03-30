import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import perfectionist from 'eslint-plugin-perfectionist'

const PERFECTIONIST_RULES = {
  'perfectionist/sort-imports': [
    'error',
    {
      type: 'natural',
      order: 'asc',
      newlinesBetween: 'always',
      groups: [
        ['builtin', 'external'],
        'internal',
        ['parent', 'sibling', 'index'],
        'object',
        'unknown'
      ]
    }
  ],
  'perfectionist/sort-objects': ['error', { type: 'natural', order: 'asc' }],
  'perfectionist/sort-interfaces': ['error', { type: 'natural', order: 'asc' }],
  'perfectionist/sort-exports': ['error', { type: 'natural', order: 'asc' }],
  'perfectionist/sort-named-exports': [
    'error',
    { type: 'natural', order: 'asc' }
  ],
  'perfectionist/sort-named-imports': [
    'error',
    { type: 'natural', order: 'asc' }
  ]
}

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      perfectionist
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...PERFECTIONIST_RULES,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true }
      ]
    },
    settings: {
      perfectionist: {
        type: 'line-length',
        partitionByComment: true
      }
    }
  }
)
