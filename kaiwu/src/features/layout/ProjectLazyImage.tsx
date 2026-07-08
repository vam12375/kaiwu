import { useEffect, useRef, useState, type SyntheticEvent } from 'react';

const MAX_ACTIVE_PROJECT_IMAGE_LOADS = 6;

let activeProjectImageLoads = 0;
const pendingProjectImageLoads: Array<() => void> = [];

function flushProjectImageQueue() {
  while (activeProjectImageLoads < MAX_ACTIVE_PROJECT_IMAGE_LOADS && pendingProjectImageLoads.length > 0) {
    pendingProjectImageLoads.shift()?.();
  }
}

function enqueueProjectImageLoad(startLoad: () => void) {
  let started = false;
  const start = () => {
    if (started) return;
    started = true;
    activeProjectImageLoads += 1;
    startLoad();
  };

  if (activeProjectImageLoads < MAX_ACTIVE_PROJECT_IMAGE_LOADS) {
    start();
  } else {
    pendingProjectImageLoads.push(start);
  }

  return () => {
    if (started) return;
    const index = pendingProjectImageLoads.indexOf(start);
    if (index >= 0) pendingProjectImageLoads.splice(index, 1);
  };
}

function releaseProjectImageLoad() {
  activeProjectImageLoads = Math.max(0, activeProjectImageLoads - 1);
  flushProjectImageQueue();
}

type ProjectLazyImageProps = {
  src: string;
  alt: string;
  className?: string;
  imageClassName?: string;
  rootMargin?: string;
  eager?: boolean;
  title?: string;
  onLoad?: (event: SyntheticEvent<HTMLImageElement>) => void;
  onError?: (event: SyntheticEvent<HTMLImageElement>) => void;
};

export function ProjectLazyImage({
  src,
  alt,
  className,
  imageClassName,
  rootMargin = '360px 0px',
  eager = false,
  title,
  onLoad,
  onError,
}: ProjectLazyImageProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cancelQueuedLoadRef = useRef<(() => void) | null>(null);
  const releaseLoadSlotRef = useRef<(() => void) | null>(null);
  const [isNearViewport, setIsNearViewport] = useState(eager);
  const [activeSrc, setActiveSrc] = useState(eager ? src : '');

  const releaseLoadSlot = () => {
    if (!releaseLoadSlotRef.current) return;
    const release = releaseLoadSlotRef.current;
    releaseLoadSlotRef.current = null;
    release();
  };

  useEffect(() => {
    setIsNearViewport(eager);
    setActiveSrc(eager ? src : '');

    return () => {
      cancelQueuedLoadRef.current?.();
      cancelQueuedLoadRef.current = null;
      releaseLoadSlot();
    };
  }, [src]);

  useEffect(() => {
    if (!eager) return;
    cancelQueuedLoadRef.current?.();
    cancelQueuedLoadRef.current = null;
    releaseLoadSlot();
    setIsNearViewport(true);
    setActiveSrc(src);
  }, [eager, src]);

  useEffect(() => {
    if (eager || isNearViewport) return;
    const container = containerRef.current;
    if (!container) return;
    if (typeof IntersectionObserver === 'undefined') {
      setIsNearViewport(true);
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      setIsNearViewport(true);
      observer.disconnect();
    }, { rootMargin });

    observer.observe(container);
    return () => observer.disconnect();
  }, [eager, isNearViewport, rootMargin]);

  useEffect(() => {
    if (eager || !isNearViewport || !src || activeSrc) return;

    const cancelQueuedLoad = enqueueProjectImageLoad(() => {
      releaseLoadSlotRef.current = releaseProjectImageLoad;
      cancelQueuedLoadRef.current = null;
      setActiveSrc(src);
    });
    cancelQueuedLoadRef.current = cancelQueuedLoad;

    return () => {
      cancelQueuedLoad();
      if (cancelQueuedLoadRef.current === cancelQueuedLoad) {
        cancelQueuedLoadRef.current = null;
      }
    };
  }, [activeSrc, eager, isNearViewport, src]);

  const handleLoad = (event: SyntheticEvent<HTMLImageElement>) => {
    releaseLoadSlot();
    onLoad?.(event);
  };

  const handleError = (event: SyntheticEvent<HTMLImageElement>) => {
    releaseLoadSlot();
    onError?.(event);
  };

  return (
    <div
      ref={containerRef}
      className={className ? `project-lazy-image ${className}` : 'project-lazy-image'}
      aria-busy={!activeSrc}
    >
      {activeSrc ? (
        <img
          className={imageClassName}
          src={activeSrc}
          alt={alt}
          title={title}
          loading={eager ? 'eager' : 'lazy'}
          decoding="async"
          fetchPriority={eager ? 'high' : 'low'}
          onLoad={handleLoad}
          onError={handleError}
        />
      ) : (
        <div className="project-lazy-image-placeholder" aria-hidden="true" />
      )}
    </div>
  );
}
