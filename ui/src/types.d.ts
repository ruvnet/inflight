declare interface ImportMeta {
  url: string;
  main: boolean;
  resolve(specifier: string): string;
}

interface TestContext {
  name: string;
  step(name: string, fn: (t: TestContext) => void | Promise<void>): Promise<void>;
  ignore(name: string, fn: (t: TestContext) => void | Promise<void>): Promise<void>;
}

// Add Jest globals
declare var jest: any;
declare var describe: (name: string, fn: () => void) => void;
declare var beforeEach: (fn: () => void | Promise<void>) => void;
declare var afterEach: (fn: () => void | Promise<void>) => void;
declare var it: (name: string, fn: () => void | Promise<void>) => void;
declare var expect: any;
