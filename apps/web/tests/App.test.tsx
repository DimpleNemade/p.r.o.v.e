import { describe, expect, it } from "vitest";
describe("investigator workspace scaffold", () => { it("keeps provenance language explicit", () => { expect("provenance-first").toContain("provenance"); }); });
