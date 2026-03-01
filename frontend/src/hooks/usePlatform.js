import { useTelegram } from './useTelegram'
import { useVK } from './useVK'

/**
 * Unified platform hook. Detects Telegram or VK environment
 * and returns a platform-agnostic user identity.
 */
export function usePlatform() {
  const tg = useTelegram()
  const vk = useVK()

  if (tg.user) {
    return {
      platform: 'telegram',
      userId: tg.user.id,
      username: tg.username || null,
      firstName: tg.firstName,
      lastName: tg.lastName,
      ready: tg.ready,
      tg,
    }
  }

  if (vk.isVK) {
    return {
      platform: 'vk',
      userId: vk.vkUserId,
      username: null,
      firstName: vk.firstName,
      lastName: vk.lastName,
      ready: vk.ready,
      vk,
    }
  }

  return {
    platform: 'web',
    userId: null,
    username: null,
    firstName: '',
    lastName: '',
    ready: tg.ready && vk.ready,
    tg,
    vk,
  }
}
