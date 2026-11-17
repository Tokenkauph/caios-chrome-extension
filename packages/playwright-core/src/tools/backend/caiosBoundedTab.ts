/**
 * CAIOS browser-tab list recovery for unresolved page operations.
 *
 * This does not bypass the extension's user tab-approval boundary.
 * Only use for best-effort read-only tab enumeration; never for actions.
 */
export async function settleWithin<T>(operation: Promise<T>, ms: number): Promise<T | undefined> {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      operation.catch(() => undefined),
      new Promise<undefined>(resolve => {
        timeout = setTimeout(() => resolve(undefined), ms);
      })
    ]);
  } finally {
    if (timeout !== undefined)
      clearTimeout(timeout);
  }
}
