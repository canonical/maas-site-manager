import { fixupConfigRules, fixupPluginRules } from "@eslint/compat";
import { FlatCompat } from "@eslint/eslintrc";
import js from "@eslint/js";
import { globalIgnores } from "eslint/config";

import noOnlyTests from "eslint-plugin-no-only-tests";
import noRelativeImportPaths from "eslint-plugin-no-relative-import-paths";
import prettier from "eslint-plugin-prettier";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import testingLibrary from "eslint-plugin-testing-library";
import unusedImports from "eslint-plugin-unused-imports";

import path from "path";
import { fileURLToPath } from "url";

import tseslint from "typescript-eslint";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

export default tseslint.config(
  [globalIgnores(["node_modules/", "dist/", ".prettierrc.js", ".eslintrc.js", "env.d.ts", "**/apiclient/", ".cache/"])],
  tseslint.configs.recommended,
  ...fixupConfigRules(
    compat.extends(
      "./.eslintrc-auto-import.json",
      "plugin:import/errors",
      "plugin:import/warnings",
      "plugin:import/typescript",
      "plugin:@tanstack/eslint-plugin-query/recommended",
      "eslint-config-prettier", // Ensure this is last in the list.
    ),
  ),
  {
    plugins: {
      "unused-imports": unusedImports,
      "no-relative-import-paths": noRelativeImportPaths,
      react,
      "react-hooks": reactHooks,
      prettier: fixupPluginRules(prettier),
    },

    languageOptions: {
      globals: {
        usabilla_live: false,
      },

      ecmaVersion: 2018,
      sourceType: "module",

      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },

    settings: {
      react: {
        version: "detect",
      },

      "import/resolver": {
        alias: {
          map: [["@", path.resolve(__dirname, "src")]],
          extensions: [".js", ".jsx", ".ts", ".tsx"],
        },

        typescript: {},

        node: {
          extensions: [".js", ".jsx", ".ts", ".tsx"],
        },
      },
    },
    rules: {
      "prettier/prettier": "error",
      complexity: "error",
      "no-relative-import-paths/no-relative-import-paths": [
        "warn",
        { allowSameFolder: true, rootDir: "frontend/src", prefix: "@" },
      ],
      "no-debugger": process.env.CI ? "error" : "warn",
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
    },
  },
  ...fixupConfigRules(
    compat.extends(
      "prettier",
      "plugin:import/errors",
      "plugin:import/warnings",
      "plugin:import/typescript",
      "plugin:prettier/recommended",
    ),
  ).map((config) => ({
    ...config,
    files: ["src/**/*.ts?(x)"],
  })),
  {
    files: ["src/**/*.ts?(x)"],
    plugins: {
      "unused-imports": unusedImports,
      react,
    },

    languageOptions: {
      ecmaVersion: 2018,
      sourceType: "module",

      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },

    settings: {
      "import/resolver": {
        node: {
          paths: ["src"],
          extensions: [".js", ".jsx", ".ts", ".tsx"],
        },
      },

      react: {
        version: "detect",
      },
    },

    rules: {
      "prettier/prettier": "error",
      "@typescript-eslint/no-unused-vars": "off",
      "unused-imports/no-unused-imports": "error",
      "@typescript-eslint/no-unused-expressions": [
        "error",
        {
          allowShortCircuit: true,
          allowTernary: true,
        },
      ],

      "unused-imports/no-unused-vars": [
        "warn",
        {
          vars: "all",
          varsIgnorePattern: "^_",
          args: "after-used",
          ignoreRestSiblings: true,
          argsIgnorePattern: "^_",
        },
      ],
      "no-restricted-imports": [
        "error",
        {
          name: "react-router",
          message: 'Use strictly typed "@/router" import instead.',
        },
        {
          name: "@testing-library/react",
          message: 'Use "@/utils/test-utils" instead.',
        },
        {
          name: "@testing-library/user-event",
          message: 'Use "@/utils/test-utils" instead.',
        },
      ],

      "@typescript-eslint/consistent-type-imports": 2,
      "import/namespace": "off",
      "import/no-named-as-default": 0,

      "import/order": [
        "error",
        {
          pathGroups: [
            {
              pattern: "react",
              group: "external",
              position: "before",
            },
            {
              pattern: "~/app",
              group: "internal",
            },
          ],

          pathGroupsExcludedImportTypes: ["react"],
          "newlines-between": "always",

          alphabetize: {
            order: "asc",
          },
        },
      ],

      "no-console": "warn",

      "react/forbid-component-props": [
        "error",
        {
          forbid: [
            {
              propName: "data-test",
              message: "Use `data-testid` instead of `data-test` attribute",
            },
          ],
        },
      ],

      "react/forbid-dom-props": [
        "error",
        {
          forbid: [
            {
              propName: "data-test",
              message: "Use `data-testid` instead of `data-test` attribute",
            },
          ],
        },
      ],

      "react/jsx-sort-props": "error",
    },
  },
  {
    files: ["src/**/*.js?(x)"],
    rules: {
      "no-unused-vars": 2,
    },
  },
  {
    files: ["src/**/*.ts?(x)"],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
      },
    },
    rules: {
      "@typescript-eslint/array-type": "error",
      "@typescript-eslint/consistent-indexed-object-style": "error",
      "@typescript-eslint/dot-notation": "error",
      "@typescript-eslint/no-confusing-void-expression": "error",
      "@typescript-eslint/no-duplicate-type-constituents": "error",
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-for-in-array": "error",
      "@typescript-eslint/no-import-type-side-effects": "error",
      "@typescript-eslint/no-inferrable-types": "error",
      "@typescript-eslint/no-unnecessary-type-arguments": "error",
      "@typescript-eslint/no-unused-expressions": "error",
      "@typescript-eslint/prefer-includes": "error",
      "@typescript-eslint/prefer-reduce-type-parameter": "error",
      "@typescript-eslint/prefer-regexp-exec": "error",
      "@typescript-eslint/restrict-plus-operands": "error",
      "@typescript-eslint/sort-type-constituents": "error",
    },
  },
  {
    files: ["src/**/*.tsx"],
    rules: {
      "react/no-multi-comp": ["error", { ignoreStateless: true }],
    },
  },
  {
    files: ["src/app/apiclient/**/*.[jt]s?(x)"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/ban-ts-comment": "off",
    },
  },
  ...compat.extends("plugin:testing-library/react").map((config) => ({
    ...config,
    files: ["src/*/*.test.[jt]s?(x)"],
  })),
  {
    files: ["src/**/*.test.[jt]s?(x)"],

    plugins: {
      "no-only-tests": noOnlyTests,
      "testing-library": testingLibrary,
    },

    rules: {
      "no-only-tests/no-only-tests": "error",
      "testing-library/await-async-queries": "error",
      "testing-library/no-await-sync-queries": "error",
      "testing-library/prefer-find-by": "off",
      "testing-library/prefer-explicit-assert": "error",

      "testing-library/prefer-user-event": [
        "error",
        {
          allowedMethods: ["change"],
        },
      ],

      "react/no-multi-comp": "off",
    },
  },
  {
    files: ["cypress/**/*.ts", "cypress/**/*.tsx"],
    rules: {
      "@typescript-eslint/no-namespace": ["error", { allowDeclarations: true }],
    },
  },
  {
    files: ["cypress/**/*.ts", "cypress/**/*.tsx"],

    plugins: {
      "no-only-tests": noOnlyTests,
    },

    rules: {
      "no-only-tests/no-only-tests": "error",
    },
  },
);
