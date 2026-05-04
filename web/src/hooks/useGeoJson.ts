import type { FeatureCollection } from "geojson";
import { useFetchJson } from "./useFetchJson";

export function useWorldGeo() {
  return useFetchJson<FeatureCollection>("/world.geojson");
}
