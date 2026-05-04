import type { ExchangesMap } from "../types";
import { useFetchJson } from "./useFetchJson";

export function useExchanges() {
  return useFetchJson<ExchangesMap>("/exchanges.json");
}
