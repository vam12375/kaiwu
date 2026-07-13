import { CheckCircle2, Download, ExternalLink, FileText, Folder } from 'lucide-react';

import type { ReportResultCard as ReportResultCardData } from '../../hooks/agentEventReducer';
import '../../styles/conversation/report-result-card.css';

type ReportResultCardProps = {
  card: ReportResultCardData;
};

export function ReportResultCard({ card }: ReportResultCardProps) {
  const folders = card.folders.length > 0 ? card.folders : ['AI 对话产出'];
  const fileType = card.fileType.toUpperCase();
  const generatedAt = card.generatedAt || '刚刚生成';
  const statusText = card.sourceLabel ? `${card.sourceLabel}已生成` : '报告已生成';

  return (
    <section className="report-result-card" aria-label={statusText}>
      <div className="report-result-card__body">
        <div className="report-result-card__icon" aria-hidden="true">
          <FileText size={22} />
        </div>
        <div className="report-result-card__main">
          <div className="report-result-card__status">
            <CheckCircle2 size={14} />
            <span>{statusText}</span>
          </div>
          <h3>{card.fileName}</h3>
          {card.title !== card.fileName && <p>{card.title}</p>}
          <div className="report-result-card__meta">
            <span>{fileType} 页面</span>
            <span>{generatedAt}</span>
          </div>
        </div>
      </div>

      <div className="report-result-card__folders" aria-label="保存位置">
        <Folder size={14} />
        <div>
          {folders.map((folder) => (
            <span key={folder}>{folder}</span>
          ))}
        </div>
      </div>

      {card.url && (
        <div className="report-result-card__actions">
          <a className="report-result-card__button report-result-card__button--primary" href={card.url} target="_blank" rel="noreferrer">
            <ExternalLink size={14} />
            <span>预览报告</span>
          </a>
          <a className="report-result-card__button" href={card.url} download={card.fileName}>
            <Download size={14} />
            <span>下载 HTML</span>
          </a>
        </div>
      )}
    </section>
  );
}
