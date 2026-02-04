
import js from '@eslint/js';
import pluginVue from 'eslint-plugin-vue';
import tseslint from 'typescript-eslint';

export default [
    {
        ignores: ['dist/*', 'node_modules/*'],
    },
    js.configs.recommended,
    ...tseslint.configs.recommended,
    ...pluginVue.configs['flat/essential'],
    {
        files: ['*.vue', '**/*.vue'],
        languageOptions: {
            parser: pluginVue.parser,
            parserOptions: {
                parser: tseslint.parser,
                sourceType: 'module',
            },
        },
    },
    {
        rules: {
            'vue/multi-word-component-names': 'off',
            '@typescript-eslint/no-explicit-any': 'off',
            '@typescript-eslint/no-unused-vars': 'off',
            '@typescript-eslint/no-unused-expressions': 'off',
            '@typescript-eslint/no-empty-object-type': 'off',
            'no-undef': 'off',
            'no-unused-vars': 'off',
            'vue/no-parsing-error': 'off'
        },
    },
];
