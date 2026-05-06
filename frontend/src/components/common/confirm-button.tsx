interface ConfirmButtonProps {
  children: string
  confirmMessage: string
  disabled?: boolean
  className: string
  onConfirm: () => void
}

export function ConfirmButton({ children, confirmMessage, disabled, className, onConfirm }: ConfirmButtonProps) {
  function handleClick() {
    if (window.confirm(confirmMessage)) {
      onConfirm()
    }
  }

  return (
    <button className={className} disabled={disabled} onClick={handleClick} type="button">
      {children}
    </button>
  )
}
