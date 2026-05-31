export default {
  mounted(el, binding) {
    el._tooltipData = {
      value: binding.value,
      arg: binding.arg || 'top'
    }
    
    let tooltipDiv = null
    
    const updatePosition = () => {
      if (!tooltipDiv) return
      
      const rect = el.getBoundingClientRect()
      // Use offsetWidth/Height if rect is 0 (can happen on initial append)
      const tw = tooltipDiv.offsetWidth
      const th = tooltipDiv.offsetHeight
      const position = el._tooltipData.arg
      const offset = 8

      let top, left

      switch (position) {
        case 'right':
          top = rect.top + (rect.height - th) / 2
          left = rect.right + offset
          break
        case 'left':
          top = rect.top + (rect.height - th) / 2
          left = rect.left - tw - offset
          break
        case 'bottom':
          top = rect.bottom + offset
          left = rect.left + (rect.width - tw) / 2
          break
        default: // top
          top = rect.top - th - offset
          left = rect.left + (rect.width - tw) / 2
      }

      // Viewport collision detection
      if (left < offset) left = offset
      if (left + tw > window.innerWidth - offset) {
        left = window.innerWidth - tw - offset
      }
      if (top < offset) top = offset
      if (top + th > window.innerHeight - offset) {
        top = window.innerHeight - th - offset
      }

      tooltipDiv.style.top = `${Math.round(top)}px`
      tooltipDiv.style.left = `${Math.round(left)}px`
    }

    const createTooltip = () => {
      // Use the latest value from el._tooltipData
      const text = el._tooltipData.value
      if (tooltipDiv || !text) return

      tooltipDiv = document.createElement('div')
      tooltipDiv.textContent = text
      tooltipDiv.className = 'custom-tooltip-box'
      
      document.body.appendChild(tooltipDiv)
      
      // Give it a tiny bit to get dimensions if needed, though usually offsetWidth works after append
      updatePosition()

      // Animate in
      requestAnimationFrame(() => {
        if (tooltipDiv) {
          tooltipDiv.classList.add('show')
          // Re-update position after it has definitely painted once
          updatePosition()
        }
      })
    }

    const removeTooltip = () => {
      if (tooltipDiv) {
        tooltipDiv.remove()
        tooltipDiv = null
      }
    }

    el.addEventListener('mouseenter', createTooltip)
    el.addEventListener('mouseleave', removeTooltip)
    el.addEventListener('click', removeTooltip)

    el._tooltipCleanup = () => {
      el.removeEventListener('mouseenter', createTooltip)
      el.removeEventListener('mouseleave', removeTooltip)
      el.removeEventListener('click', removeTooltip)
      removeTooltip()
    }
  },
  updated(el, binding) {
    // Update the stored data so listeners have latest values
    el._tooltipData = {
      value: binding.value,
      arg: binding.arg || 'top'
    }
    
    // If value becomes falsy while potentially hovering, remove existing tooltip
    if (!binding.value) {
      // We don't have direct access to tooltipDiv here, 
      // but the mouseleave listener or another hover will naturally handle it.
      // To be immediate, we'll trigger the cleanup's internal removal if we could,
      // but searching by text is the only way if we don't store tooltipDiv on el.
      const divs = document.querySelectorAll('.fixed.z-\\[9999\\]')
      divs.forEach(d => {
        if (d.textContent === binding.oldValue) d.remove()
      })
    }
  },
  unmounted(el) {
    if (el._tooltipCleanup) {
      el._tooltipCleanup()
    }
  }
}
