import { ChevronLeft, ChevronRight, Download, ImageOff, X } from 'lucide-react';
import { useEffect, useState, type SyntheticEvent } from 'react';

import { API_BASE_URL } from '../../api/client';
import type { ProjectImage } from '../../types';
import { ProjectLazyImage } from './ProjectLazyImage';
import '../../styles/modals/modal-base.css';
import '../../styles/project/project-image-preview.css';

type ProjectImagePreviewModalProps = {
  images: ProjectImage[];
  currentIndex: number;
  onChange: (index: number) => void;
  onClose: () => void;
};

type ImageFitMode = 'portrait' | 'landscape' | 'square';

function formatImageSize(size?: number) {
  if (typeof size !== 'number') return '未知大小';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function imageDownloadUrl(imageUrl: string) {
  return `${API_BASE_URL}/api/download-image?url=${encodeURIComponent(imageUrl)}`;
}

function inferFitMode(width: number, height: number): ImageFitMode {
  if (width <= 0 || height <= 0) return 'landscape';
  const ratio = height / width;
  if (ratio >= 1.35) return 'portrait';
  if (ratio <= 0.85) return 'landscape';
  return 'square';
}

function inferFitModeFromRatio(ratio?: string): ImageFitMode | null {
  if (!ratio) return null;
  const [widthText, heightText] = ratio.split(':');
  const width = Number(widthText);
  const height = Number(heightText);
  if (!Number.isFinite(width) || !Number.isFinite(height)) return null;
  return inferFitMode(width, height);
}

export function ProjectImagePreviewModal({
  images,
  currentIndex,
  onChange,
  onClose,
}: ProjectImagePreviewModalProps) {
  const safeIndex = Math.min(Math.max(currentIndex, 0), Math.max(images.length - 1, 0));
  const image = images[safeIndex];
  const [imageFailed, setImageFailed] = useState(false);
  const [imageFitMode, setImageFitMode] = useState<ImageFitMode>('landscape');

  useEffect(() => {
    if (images.length > 0 && safeIndex !== currentIndex) {
      onChange(safeIndex);
    }
  }, [currentIndex, images.length, onChange, safeIndex]);

  useEffect(() => {
    setImageFailed(false);
    setImageFitMode(inferFitModeFromRatio(image?.ratio) || 'landscape');
  }, [image?.ratio, image?.url]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }
      if (event.key === 'ArrowLeft' && safeIndex > 0) {
        onChange(safeIndex - 1);
        return;
      }
      if (event.key === 'ArrowRight' && safeIndex < images.length - 1) {
        onChange(safeIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [images.length, onChange, onClose, safeIndex]);

  if (!image) return null;

  const title = image.style || image.name;
  const canGoPrevious = safeIndex > 0;
  const canGoNext = safeIndex < images.length - 1;
  const metadataRows = [
    ['模型', image.model || '未知模型'],
    ['比例', image.ratio || '未知比例'],
    ['画质', image.resolution || '未知画质'],
    ['大小', formatImageSize(image.size)],
    ['更新时间', image.modified || image.created_at || '未知时间'],
    ['来源', image.source || '图片库'],
  ];

  if (typeof image.reference_count === 'number' && image.reference_count > 0) {
    metadataRows.push(['参考图', `${image.reference_count} 张`]);
  }

  const openDownload = () => {
    window.open(imageDownloadUrl(image.original_url || image.url), '_blank', 'noopener,noreferrer');
  };
  const handleImageLoad = (event: SyntheticEvent<HTMLImageElement>) => {
    const loadedImage = event.currentTarget;
    setImageFitMode(inferFitMode(loadedImage.naturalWidth, loadedImage.naturalHeight));
  };

  return (
    <div className="modal-backdrop project-image-preview-backdrop" onClick={onClose}>
      <section
        className="project-image-preview-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="图片预览"
      >
        <div className="project-image-preview-stage">
          <button
            className="project-image-nav project-image-nav-left"
            onClick={() => canGoPrevious && onChange(safeIndex - 1)}
            type="button"
            aria-label="上一张图片"
            title="上一张"
            disabled={!canGoPrevious}
          >
            <ChevronLeft size={24} />
          </button>
          <div className="project-image-preview-canvas">
            {imageFailed ? (
              <div className="project-image-preview-error">
                <ImageOff size={34} />
                <strong>图片加载失败</strong>
              </div>
            ) : (
              <img
                className={`project-image-preview-img is-${imageFitMode}`}
                src={image.url}
                alt={title}
                onLoad={handleImageLoad}
                onError={() => setImageFailed(true)}
              />
            )}
          </div>
          <button
            className="project-image-nav project-image-nav-right"
            onClick={() => canGoNext && onChange(safeIndex + 1)}
            type="button"
            aria-label="下一张图片"
            title="下一张"
            disabled={!canGoNext}
          >
            <ChevronRight size={24} />
          </button>
        </div>

        <aside className="project-image-preview-info">
          <header className="project-image-preview-tools">
            <button className="project-image-close" onClick={onClose} type="button" aria-label="关闭预览" title="关闭">
              <X size={20} />
            </button>
            <button className="project-image-download" onClick={openDownload} type="button">
              <Download size={16} />
              下载
            </button>
          </header>

          <div className="project-image-thumbnail-strip" aria-label="图片缩略图">
            {images.map((item, index) => (
              <button
                key={item.name}
                className={index === safeIndex ? 'active' : ''}
                onClick={() => onChange(index)}
                type="button"
                aria-label={`查看图片 ${index + 1}`}
                title={item.style || item.name}
              >
                <ProjectLazyImage
                  src={item.url}
                  alt={item.style || item.name}
                  rootMargin="120px"
                  eager={index === safeIndex}
                />
              </button>
            ))}
          </div>

          <div className="project-image-prompt-block">
            <span>图片提示词</span>
            <p>{image.prompt || '暂无提示词信息'}</p>
          </div>

          <dl className="project-image-meta-list">
            {metadataRows.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </aside>
      </section>
    </div>
  );
}
