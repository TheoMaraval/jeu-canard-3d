import globals from 'globals';

// Garde-fou : un nom utilisé mais ni déclaré ni importé (Vite et les tests ne le voient pas).
export default [{
  files: ['src/**/*.js', 'tests/**/*.js'],
  languageOptions: { ecmaVersion: 'latest', sourceType: 'module', globals: { ...globals.browser, ...globals.node } },
  rules: { 'no-undef': 'error', 'no-unused-vars': 'warn' },
}];
