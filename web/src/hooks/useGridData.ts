import type { GridDataFile } from "../types";
import { useFetchJson } from "./useFetchJson";

export function useGridData() {
  return useFetchJson<GridDataFile>("/mock-data.json");
}
