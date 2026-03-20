/**
 * Button 组件测试示例
 */

import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

describe('Button Component (Example)', () => {
  it('should render button with correct text', () => {
    const { getByText } = render(
      <button type="button" onClick={() => {}}>
        Click me
      </button>
    )
    expect(getByText('Click me')).toBeInTheDocument()
  })

  it('should call onClick handler when clicked', async () => {
    const handleClick = vi.fn()
    const { getByRole } = render(
      <button type="button" onClick={handleClick}>
        Click me
      </button>
    )

    const button = getByRole('button')
    await userEvent.click(button)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should be disabled when disabled prop is true', () => {
    const { getByRole } = render(
      <button type="button" disabled>
        Disabled
      </button>
    )

    const button = getByRole('button')
    expect(button).toBeDisabled()
  })
})
