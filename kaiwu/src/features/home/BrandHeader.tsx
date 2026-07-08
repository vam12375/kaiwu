import { Box } from 'lucide-react';
import '../../styles/home/brand-header.css';

export function BrandHeader() {
  return (
    <section className="brand-header">
      <div className="brand-header-inner">
        <div className="brand-logo-row">
          <div className="brand-logo-icon">
            <Box size={20} />
          </div>
          <span className="brand-name">开物</span>
        </div>
        <h1 className="brand-subtitle">点击下方卡片，快捷开始创业计划</h1>
      </div>
    </section>
  );
}
