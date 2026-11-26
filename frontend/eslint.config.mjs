// ESLint flat config. Keeps the rule sets of the former .eslintrc.yml:
// ESLint recommended, typescript-eslint recommended and React recommended.
// React rules come from @eslint-react because eslint-plugin-react does
// not support ESLint 10.
import js from "@eslint/js";
import eslintReact from "@eslint-react/eslint-plugin";
import { defineConfig } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  { ignores: ["dist/", ".parcel-cache/"] },
  {
    files: ["src/**/*.{js,jsx,ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      eslintReact.configs.recommended,
    ],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser,
    },
  },
]);
