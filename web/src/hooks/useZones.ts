import type { ZonesMap } from "../types";
import { useFetchJson } from "./useFetchJson";

export function useZones() {
  return useFetchJson<ZonesMap>("/zones.json");
}
