import * as UAParserNS from 'ua-parser-js'
const UAParser = UAParserNS.UAParser

export function collectClientData() {
  if (typeof navigator === 'undefined') {
    return {
      device_type: 'unknown',
      browser: 'unknown',
      browser_version: '',
      resolution: '0x0',
      language: '',
    }
  }
  const parser = new UAParser()
  const { type } = parser.getDevice()
  const { name: browserName, version: browserVersion } = parser.getBrowser()
  const deviceType = type === 'mobile' || type === 'tablet' ? type : 'desktop'
  const w = typeof screen !== 'undefined' ? screen.width : 0
  const h = typeof screen !== 'undefined' ? screen.height : 0
  const lang = navigator.language || navigator.userLanguage || ''
  return {
    device_type: deviceType || 'desktop',
    browser: browserName || 'unknown',
    browser_version: browserVersion || '',
    resolution: `${w}x${h}`,
    language: lang,
  }
}
