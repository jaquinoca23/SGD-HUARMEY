import { useCallback, useEffect, useState } from "react";

import { errorMessage } from "../services/http";
import type { Paginated } from "../types";

type Fetcher<T> = (params: Record<string, string | number | boolean | undefined>) => Promise<Paginated<T>>;

/** Lista paginada con búsqueda (con retardo) y recarga manual. */
export function useList<T>(fetcher: Fetcher<T>, extra: Record<string, string | number | boolean | undefined> = {}, pageSize = 10) {
  const [items, setItems] = useState<T[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const extraKey = JSON.stringify(extra);

  useEffect(() => {
    const id = setTimeout(() => {
      setDebounced(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(id);
  }, [search]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetcher({ ...extra, page, page_size: pageSize, search: debounced || undefined })
      .then((data) => {
        if (cancelled) return;
        setItems(data.results);
        setCount(data.count);
        setError(null);
      })
      .catch((e) => !cancelled && setError(errorMessage(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, debounced, tick, extraKey, pageSize]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { items, count, page, setPage, search, setSearch, loading, error, reload, pageSize };
}
