import { useCallback, useRef, useState } from "react";
import { fetchProducts } from "../api/products";
import type { Product } from "../types/product";

interface UseProductsFetchProps {
  latitude?: number;
  longitude?: number;
  query?: string;
  marketId?: number;
}

export function useProductsFetch(props: UseProductsFetchProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [hasMoreData, setHasMoreData] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const propsRef = useRef(props);
  propsRef.current = props;

  const pageRef = useRef(1);
  const hasMoreDataRef = useRef(true);
  const isLoadingRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(
    async (queryOverride?: string, reset = false) => {
      if (reset) {
        abortControllerRef.current?.abort();
        pageRef.current = 1;
        hasMoreDataRef.current = true;
        setProducts([]);
        setHasMoreData(true);
      } else if (!hasMoreDataRef.current || isLoadingRef.current) {
        return;
      }

      isLoadingRef.current = true;
      setIsLoading(true);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const query =
        queryOverride !== undefined ? queryOverride : propsRef.current.query;
      const normalizedQuery = query?.trim() || undefined;

      try {
        const response = await fetchProducts(
          propsRef.current.latitude || 0,
          propsRef.current.longitude || 0,
          pageRef.current,
          normalizedQuery,
          propsRef.current.marketId,
          controller.signal,
        );

        if (controller.signal.aborted) return;

        const newProducts = response.results || [];

        if (newProducts.length > 0) {
          setProducts((current) => [...current, ...newProducts]);
          pageRef.current += 1;
          if (!response.next) hasMoreDataRef.current = false;
        } else {
          hasMoreDataRef.current = false;
        }
        setHasMoreData(hasMoreDataRef.current);
      } catch (_error) {
        if (controller.signal.aborted) return;
        hasMoreDataRef.current = false;
        setHasMoreData(false);
      } finally {
        if (!controller.signal.aborted) {
          isLoadingRef.current = false;
          setIsLoading(false);
        }
      }
    },
    [],
  );

  const resetPagination = useCallback(() => {
    abortControllerRef.current?.abort();
    pageRef.current = 1;
    hasMoreDataRef.current = true;
    isLoadingRef.current = false;
    setProducts([]);
    setHasMoreData(true);
    setIsLoading(false);
  }, []);

  return {
    products,
    isLoading,
    hasMoreData,
    fetchData,
    resetPagination,
  };
}
