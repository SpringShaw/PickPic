/**
 * 弹窗遮罩层安全关闭 composable
 *
 * 解决 @click.self 在用户拖选文字超出弹窗范围时误触发关闭的问题。
 * 使用 mousedown + click 双事件跟踪，确保起点和终点都在遮罩层上才触发关闭。
 */
import { ref } from 'vue'

export function useOverlayClose(emitClose) {
  const overlayMouseDown = ref(false)

  function onOverlayMouseDown() {
    overlayMouseDown.value = true
  }

  function onOverlayClick() {
    if (overlayMouseDown.value) {
      overlayMouseDown.value = false
      emitClose()
    }
    overlayMouseDown.value = false
  }

  return { onOverlayMouseDown, onOverlayClick }
}
