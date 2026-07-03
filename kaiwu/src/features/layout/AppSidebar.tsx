import type { Dispatch, SetStateAction } from 'react';
import { Box, ChevronDown, ChevronLeft, Search, Settings2 } from 'lucide-react';

import { sidebarItems } from '../../data';
import type { ConvHistory, SidebarPage } from '../../types';
import { SidebarHistory } from '../chat/SidebarHistory';

type ResetConversationOptions = {
  activePage?: SidebarPage;
  clearLoading?: boolean;
  imageMode?: boolean;
  inputText?: string;
  open?: boolean;
};

type AppSidebarProps = {
  accountMenuOpen: boolean;
  activePage: SidebarPage;
  convHistory: ConvHistory[];
  deleteConversation: (conversationId: number, event?: React.MouseEvent<HTMLButtonElement>) => void;
  expertExpanded: boolean;
  loadConversation: (conversationId: number) => void;
  openHistoryMenu: number | null;
  openHomeConversation: () => void;
  renameConversation: (conversationId: number, title: string) => void;
  resetConversation: (options?: ResetConversationOptions) => void;
  setAccountMenuOpen: Dispatch<SetStateAction<boolean>>;
  setActivePage: Dispatch<SetStateAction<SidebarPage>>;
  setConversationOpen: Dispatch<SetStateAction<boolean>>;
  setExpertExpanded: Dispatch<SetStateAction<boolean>>;
  setOpenHistoryMenu: Dispatch<SetStateAction<number | null>>;
  setRechargeModalOpen: Dispatch<SetStateAction<boolean>>;
  setSidebarCollapsed: Dispatch<SetStateAction<boolean>>;
};

export function AppSidebar({
  accountMenuOpen,
  activePage,
  convHistory,
  deleteConversation,
  expertExpanded,
  loadConversation,
  openHistoryMenu,
  openHomeConversation,
  renameConversation,
  resetConversation,
  setAccountMenuOpen,
  setActivePage,
  setConversationOpen,
  setExpertExpanded,
  setOpenHistoryMenu,
  setRechargeModalOpen,
  setSidebarCollapsed,
}: AppSidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <Box size={16} />
          </div>
          <span className="sidebar-brand-name">开物</span>
        </div>
        <div className="sidebar-tools">
          <button onClick={() => setSidebarCollapsed(true)} type="button" aria-label="折叠侧边栏" title="折叠侧边栏">
            <ChevronLeft size={14} />
          </button>
        </div>
      </div>

      <div className="sidebar-search">
        <Search size={14} />
        <input placeholder="搜索对话和生成图片比例" />
      </div>

      <nav className="sidebar-nav">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.key || (item.key === 'home' && activePage === 'settings');
          return (
            <div key={item.label} className="sidebar-nav-group">
              <button
                className={isActive ? 'sidebar-item active' : 'sidebar-item'}
                onClick={() => {
                  if (item.key === 'home') {
                    openHomeConversation();
                    return;
                  }
                  if (item.key === 'expert') {
                    setExpertExpanded((value) => !value);
                    return;
                  }
                  if (item.key === 'skills' || item.key === 'projects') {
                    setConversationOpen(false);
                    setActivePage(item.key);
                  }
                }}
                type="button"
              >
                {Icon ? <Icon size={14} /> : <span className="sidebar-dot" />}
                <span>{item.label}</span>
                {item.key === 'expert' && <ChevronDown className={expertExpanded ? 'sidebar-chevron open' : 'sidebar-chevron'} size={13} />}
              </button>
              {item.key === 'expert' && expertExpanded && (
                <div className="expert-subnav">
                  <button onClick={() => resetConversation({ inputText: '帮我设计品牌Logo：', imageMode: true, open: true, activePage: 'home' })} type="button">
                    AI生图
                  </button>
                  <button onClick={() => resetConversation({ inputText: '帮我生成品牌宣传视频素材：', imageMode: false, open: true, activePage: 'home' })} type="button">
                    AI视频
                  </button>
                  <button
                    onClick={() => {
                      setConversationOpen(false);
                      setActivePage('coding');
                    }}
                    type="button"
                  >
                    AI编程
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <SidebarHistory
        conversations={convHistory}
        openHistoryMenu={openHistoryMenu}
        setOpenHistoryMenu={setOpenHistoryMenu}
        loadConversation={loadConversation}
        deleteConversation={deleteConversation}
        renameConversation={renameConversation}
      />

      <div className="sidebar-footer account-footer">
        {accountMenuOpen && (
          <div className="account-popover">
            <div className="account-credit-card">
              <span>剩余积分</span>
              <strong>1,280</strong>
            </div>
            <button onClick={() => setRechargeModalOpen(true)} type="button">
              <span>
                <span className="account-menu-icon">+</span>积分充值
              </span>
            </button>
            <button
              onClick={() => {
                setAccountMenuOpen(false);
                setConversationOpen(false);
                setActivePage('settings');
              }}
              type="button"
            >
              <span>
                <Settings2 size={14} />设置
              </span>
            </button>
            <button
              onClick={() => {
                setAccountMenuOpen(false);
                window.open('https://docs.kaiwu.ai', '_blank');
              }}
              type="button"
            >
              <span>
                <span className="account-menu-icon">?</span>帮助
              </span>
            </button>
            <button
              onClick={() => {
                setAccountMenuOpen(false);
                window.location.reload();
              }}
              type="button"
            >
              <span>
                <span className="account-menu-icon">↻</span>检查更新
              </span>
            </button>
            <div className="account-divider" />
            <button
              className="logout-row"
              onClick={() => {
                localStorage.clear();
                setAccountMenuOpen(false);
                resetConversation({ activePage: 'home' });
              }}
              type="button"
            >
              <span>
                <span className="account-menu-icon">↪</span>退出登录
              </span>
            </button>
          </div>
        )}
        <div className="account-bottom-wrap">
          <div className="points-inline account-points">
            <span>剩余积分</span>
            <strong>1,280</strong>
          </div>
          <button className="footer-badge account-trigger" onClick={() => setAccountMenuOpen((value) => !value)} type="button">
            <span className="footer-avatar">曜</span>
            <span>OPC创业者</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
