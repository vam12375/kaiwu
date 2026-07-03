import { WORKFLOW_STEPS } from '../../data';

export function WorkflowSteps() {
  return (
    <div className="workflow-steps">
      <div className="workflow-steps-header">
        <div className="workflow-steps-icon">?</div>
        <span>使用流程</span>
      </div>
      <div className="workflow-steps-list">
        <div className="workflow-steps-line" />
        {WORKFLOW_STEPS.map((step) => (
          <div key={step.id} className="workflow-step-item">
            <div className={step.isActive ? 'workflow-step-dot active' : 'workflow-step-dot'}>
              <span>{step.stepNumber}</span>
            </div>
            <span className={step.isActive ? 'workflow-step-title active' : 'workflow-step-title'}>
              {step.title}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
