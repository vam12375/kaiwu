import type { Dispatch, MouseEvent, SetStateAction } from 'react';

import type { ConvHistory } from '../../types';

type SidebarHistoryProps = {
  conversations: ConvHistory[];
  emptyMessage?: string;
  openHistoryMenu: number | null;
  setOpenHistoryMenu: Dispatch<SetStateAction<number | null>>;
  loadConversation: (conversationId: number) => void;
  deleteConversation: (conversationId: number, event?: MouseEvent<HTMLButtonElement>) => void;
  renameConversation: (conversationId: number, title: string) => void;
};

export function SidebarHistory({
  conversations,
  emptyMessage = '暂无对话记录',
  openHistoryMenu,
  setOpenHistoryMenu,
  loadConversation,
  deleteConversation,
  renameConversation,
}: SidebarHistoryProps) {
  return (
    <section className="history-block">
      <div className="history-heading">对话历史</div>
      <div className="history-list">
        {conversations.length === 0 && (
          <div className="history-empty">{emptyMessage}</div>
        )}
        {conversations.map((item, index) => (
          <div key={item.id} className="history-row">
            <button className="history-item" onClick={() => loadConversation(item.id)} type="button">
              <span className="history-title">{item.title}</span>
              <span className="history-tag-badge tag-对话">{item.message_count}条</span>
            </button>
            <button
              className="history-menu-button"
              onClick={(event) => {
                event.stopPropagation();
                setOpenHistoryMenu((value) => (value === index ? null : index));
              }}
              type="button"
            >
              ⋯
            </button>
            {openHistoryMenu === index && (
              <div className="history-menu-popover">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    const name = prompt('新名称：', item.title);
                    if (name && name.trim()) {
                      renameConversation(item.id, name.trim());
                    }
                  }}
                >
                  重命名
                </button>
                <button type="button" onClick={(event) => deleteConversation(item.id, event)}>
                  删除
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
