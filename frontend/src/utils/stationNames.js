// 气象站 & 国家/地区 英→中 映射
const STATION_CN = {
  // 南极洲
  'AMUNDSEN SCOTT, AY':'阿蒙森-斯科特站','VOSTOK, AY':'东方站','CONCORDIA, AQ':'康科迪亚站',
  'DOME C II, AQ':'冰穹C二号','MARBLE POINT, AY':'大理石角','HALLEY, AY':'哈雷站',
  'BALDRICK AWS, AY':'鲍德里克站','CAPE PHILLIPS, AY':'菲利普斯角',
  'DOME PLATEAU DOME A, AY':'冰穹A','DOME PLATEAU EAGLE, AY':'冰穹鹰',
  'HALVFARRYGGEN EP11, AY':'半脊EP11','LAW DOME SUMMIT, AY':'劳穹顶',
  'MID POINT, AY':'中点站','PRIESTLEY GLACIER, AY':'普里斯特利冰川',
  'S.A.N.A.E. AWS, AY':'南非科考站','UNIVERSITY WI ID 8917 SKI BLU, AY':'威大8917站',
  'UNIVERSITY WI ID 8925 LIMBERT AWS, AY':'威大8925站',
  // 中国
  'BEIJING/PEKING, CH':'北京','SHANGHAI, CH':'上海','GUANGZHOU, CH':'广州',
  'HARBIN, CH':'哈尔滨','URUMQI, CH':'乌鲁木齐','LHASA, CH':'拉萨',
  'KUNMING, CH':'昆明','CHENGDU, CH':'成都','WUHAN, CH':'武汉',
  'NANJING, CH':'南京','XIAN, CH':'西安','SHENYANG, CH':'沈阳',
  'HONG KONG INTERNATIONAL, HK':'香港','MACAU, MC':'澳门','TAIBEI, TW':'台北',
  // 亚洲主要城市
  'TOKYO, JA':'东京','OSAKA, JA':'大阪','SAPPORO, JA':'札幌','NAHA, JA':'那霸',
  'SEOUL, KS':'首尔','BUSAN, KS':'釜山','PYONGYANG, KN':'平壤',
  'BANGKOK, TH':'曼谷','CHIANG MAI, TH':'清迈','PHUKET, TH':'普吉',
  'SINGAPORE, SN':'新加坡','KUALA LUMPUR, MY':'吉隆坡',
  'JAKARTA, ID':'雅加达','SURABAYA, ID':'泗水','MEDAN, ID':'棉兰',
  'MANILA, PH':'马尼拉','DAVAO, PH':'达沃',
  'HANOI, VS':'河内','HO CHI MINH, VS':'胡志明市',
  'YANGON, BM':'仰光','MANDALAY, BM':'曼德勒',
  'NEW DELHI, IN':'新德里','MUMBAI, IN':'孟买','KOLKATA, IN':'加尔各答',
  'CHENNAI, IN':'金奈','BANGALORE, IN':'班加罗尔',
  'KARACHI, PK':'卡拉奇','LAHORE, PK':'拉合尔','ISLAMABAD, PK':'伊斯兰堡',
  'DHAKA, BG':'达卡','CHITTAGONG, BG':'吉大港',
  'COLOMBO, CE':'科伦坡','KATHMANDU, NP':'加德满都',
  'ULAANBAATAR, MG':'乌兰巴托','ASTANA, KZ':'阿斯塔纳',
  'TASHKENT, UZ':'塔什干','ALMATY, KZ':'阿拉木图',
  'TEHRAN, IR':'德黑兰','BAGHDAD, IQ':'巴格达',
  'RIYADH, SD':'利雅得','JEDDAH, SD':'吉达','DUBAI, AE':'迪拜',
  'ABU DHABI, AE':'阿布扎比','MUSCAT, MU':'马斯喀特',
  'DOHA, QA':'多哈','KUWAIT, KW':'科威特城',
  'JERUSALEM, IS':'耶路撒冷','TEL AVIV, IS':'特拉维夫',
  'ANKARA, TU':'安卡拉','ISTANBUL, TU':'伊斯坦布尔',
  // 欧洲
  'LONDON, UK':'伦敦','MANCHESTER, UK':'曼彻斯特','EDINBURGH, UK':'爱丁堡',
  'PARIS, FR':'巴黎','MARSEILLE, FR':'马赛','LYON, FR':'里昂',
  'BERLIN, GM':'柏林','FRANKFURT, GM':'法兰克福','MUNICH, GM':'慕尼黑',
  'ROME, IT':'罗马','MILAN, IT':'米兰','NAPLES, IT':'那不勒斯',
  'MADRID, SP':'马德里','BARCELONA, SP':'巴塞罗那',
  'LISBON, PO':'里斯本','PORTO, PO':'波尔图',
  'AMSTERDAM, NL':'阿姆斯特丹','ROTTERDAM, NL':'鹿特丹',
  'BRUSSELS, BX':'布鲁塞尔','VIENNA, AT':'维也纳',
  'ZURICH, SW':'苏黎世','GENEVA, SW':'日内瓦',
  'PRAGUE, CZ':'布拉格','WARSAW, PL':'华沙',
  'BUDAPEST, HU':'布达佩斯','BUCHAREST, RO':'布加勒斯特',
  'ATHENS, GR':'雅典','STOCKHOLM, SW':'斯德哥尔摩',
  'OSLO, NO':'奥斯陆','COPENHAGEN, DN':'哥本哈根',
  'HELSINKI, FI':'赫尔辛基','MOSCOW, RS':'莫斯科',
  'SAINT PETERSBURG, RS':'圣彼得堡',
  'KIEV, UP':'基辅','MINSK, BO':'明斯克',
  'DUBLIN, IE':'都柏林','REYKJAVIK, IL':'雷克雅未克',
  // 非洲
  'CAIRO, EG':'开罗','ALEXANDRIA, EG':'亚历山大',
  'LAGOS, NI':'拉各斯','ABUJA, NI':'阿布贾',
  'NAIROBI, KN':'内罗毕','MOMBASA, KN':'蒙巴萨',
  'ADDIS ABABA, ET':'亚的斯亚贝巴',
  'CAPE TOWN, ZA':'开普敦','JOHANNESBURG, ZA':'约翰内斯堡',
  'PRETORIA, ZA':'比勒陀利亚','DURBAN, ZA':'德班',
  'ALGIERS, AG':'阿尔及尔','TUNIS, TS':'突尼斯',
  'CASABLANCA, MC':'卡萨布兰卡','RABAT, MC':'拉巴特',
  'TRIPOLI, LY':'的黎波里','KHARTOUM, SU':'喀土穆',
  'DAKAR, SG':'达喀尔','ACCRA, GH':'阿克拉',
  'ANTANANARIVO, MA':'塔那那利佛',
  // 北美洲
  'NEW YORK, US':'纽约','LOS ANGELES, US':'洛杉矶','CHICAGO, US':'芝加哥',
  'HOUSTON, US':'休斯顿','MIAMI, US':'迈阿密','SAN FRANCISCO, US':'旧金山',
  'SEATTLE, US':'西雅图','BOSTON, US':'波士顿','ATLANTA, US':'亚特兰大',
  'WASHINGTON, US':'华盛顿','DALLAS, US':'达拉斯','DENVER, US':'丹佛',
  'PHOENIX, US':'凤凰城','DETROIT, US':'底特律','ANCHORAGE, US':'安克雷奇',
  'HONOLULU, US':'檀香山','NEW ORLEANS, US':'新奥尔良',
  'TORONTO, CA':'多伦多','VANCOUVER, CA':'温哥华','MONTREAL, CA':'蒙特利尔',
  'OTTAWA, CA':'渥太华','CALGARY, CA':'卡尔加里',
  'MEXICO CITY, MX':'墨西哥城','CANCUN, MX':'坎昆',
  'HAVANA, CU':'哈瓦那','KINGSTON, JM':'金斯敦',
  // 南美洲
  'SAO PAULO, BZ':'圣保罗','RIO DE JANEIRO, BZ':'里约热内卢',
  'BRASILIA, BZ':'巴西利亚','MANAUS, BZ':'马瑙斯',
  'BUENOS AIRES, AG':'布宜诺斯艾利斯','CORDOBA, AG':'科尔多瓦',
  'SANTIAGO, CI':'圣地亚哥','LIMA, PR':'利马',
  'BOGOTA, CO':'波哥大','MEDELLIN, CO':'麦德林',
  'CARACAS, VN':'加拉加斯','QUITO, EQ':'基多',
  'MONTEVIDEO, UY':'蒙得维的亚','ASUNCION, PY':'亚松森',
  // 大洋洲
  'SYDNEY, AS':'悉尼','MELBOURNE, AS':'墨尔本','BRISBANE, AS':'布里斯班',
  'PERTH, AS':'珀斯','ADELAIDE, AS':'阿德莱德','CANBERRA, AS':'堪培拉',
  'DARWIN, AS':'达尔文','HOBART, AS':'霍巴特','CAIRNS, AS':'凯恩斯',
  'AUCKLAND, NZ':'奥克兰','WELLINGTON, NZ':'惠灵顿',
  'CHRISTCHURCH, NZ':'基督城','QUEENSTOWN, NZ':'皇后镇',
  'SUVA, FJ':'苏瓦','PORT MORESBY, NG':'莫尔兹比港',
  // 特殊站点
  'ARAFAT, SA':'阿拉法特','SITEKI, WZ':'锡泰基',
  'MAHABALESHWAR, IN':'默哈伯莱什沃尔','HONAVAR, IN':'霍纳瓦尔',
  'JOKKMOKK FPL, SW':'约克莫克','KHLONG YAI, TH':'空艾',
  'KAYES DAG DAG, ML':'卡伊','MINA, SA':'米纳',
  'KOSRAE INTERNATIONAL AIRPORT, FM FM':'科斯雷机场',
  'MATAM OURO SOGUI, SG':'马塔姆','PREAH VIHEAR, CB':'柏威夏',
  'PODOR, SG':'波多尔','NARA KEIBANE, ML':'纳拉',
  'YELIMANE, ML':'耶利马内','LINGUERE, SG':'林盖尔',
  'TAMBACOUNDA, SG':'坦巴昆达','TILLABERY, NG':'蒂拉贝里',
  'NIORO DU SAHEL, ML':'纽罗','BERNARD HARBOUR, CA':'伯纳德港',
  'COLVILLE LAKE NWT, CA':'科尔维尔湖','DAWEI, BM':'土瓦',
  'YE, BM':'耶','MAO, CD':'马奥','ZAKATALA, AJ':'扎卡塔拉',
  'GAVAR, AM':'加瓦尔','FAHUD AUT, MU':'法胡德',
  'HALIM PERDANAKUSUMA INTERNATIONAL, ID':'哈利姆机场',
  'KOKONAO TIMUKA, ID':'科科纳奥','SAM RATULANGI, ID':'萨姆拉图兰吉',
  'SANTO PEKOA INTERNATIONAL, NH':'桑托佩可亚','OSMANY INTERNATIONAL, BG':'奥斯曼尼机场',
  'MILFORD SOUNDN AWS, NZ':'米尔福德峡湾','SECRETARY ISLAND AWS, NZ':'秘书岛',
  // 常见后缀替换
}

// 后缀国家代码 → 中文
const COUNTRY_CN = {
  ', CH':'中国',', HK':'中国香港',', MC':'中国澳门',', TW':'中国台湾',
  ', JA':'日本',', KS':'韩国',', KN':'朝鲜',
  ', TH':'泰国',', VN':'越南',', VS':'越南',', BM':'缅甸',
  ', IN':'印度',', PK':'巴基斯坦',', BG':'孟加拉国',', CE':'斯里兰卡',
  ', NP':'尼泊尔',', MG':'蒙古',', KZ':'哈萨克斯坦',', UZ':'乌兹别克斯坦',
  ', IR':'伊朗',', IQ':'伊拉克',', SD':'沙特阿拉伯',', SA':'沙特阿拉伯',
  ', AE':'阿联酋',', MU':'阿曼',', QA':'卡塔尔',', KW':'科威特',
  ', IS':'以色列',', TU':'土耳其',', SY':'叙利亚',', JO':'约旦',
  ', ID':'印度尼西亚',', MY':'马来西亚',', SN':'新加坡',
  ', PH':'菲律宾',', CB':'柬埔寨',', LA':'老挝',
  ', UK':'英国',', FR':'法国',', GM':'德国',', IT':'意大利',
  ', SP':'西班牙',', PO':'葡萄牙',', NL':'荷兰',', BX':'比利时',
  ', AT':'奥地利',', SW':'瑞士',', CZ':'捷克',', PL':'波兰',
  ', HU':'匈牙利',', RO':'罗马尼亚',', GR':'希腊',
  ', NO':'挪威',', DN':'丹麦',', FI':'芬兰',', RS':'俄罗斯',
  ', UP':'乌克兰',', BO':'白俄罗斯',', IE':'爱尔兰',', IL':'冰岛',
  ', US':'美国',', CA':'加拿大',', MX':'墨西哥',', CU':'古巴',', JM':'牙买加',
  ', BZ':'巴西',', AG':'阿根廷',', CI':'智利',', PR':'秘鲁',
  ', CO':'哥伦比亚',', VN':'委内瑞拉',', EQ':'厄瓜多尔',
  ', UY':'乌拉圭',', PY':'巴拉圭',', GY':'圭亚那',
  ', AS':'澳大利亚',', NZ':'新西兰',', FJ':'斐济',', NG':'巴布亚新几内亚',
  ', EG':'埃及',', NI':'尼日利亚',', ET':'埃塞俄比亚',
  ', ZA':'南非',', TS':'突尼斯',', LY':'利比亚',
  ', SU':'苏丹',', SG':'塞内加尔',', GH':'加纳',
  ', MA':'马达加斯加',', ML':'马里',', CD':'乍得',
  ', KE':'肯尼亚',', TZ':'坦桑尼亚',', UG':'乌干达',
  ', AO':'安哥拉',', MZ':'莫桑比克',', ZM':'赞比亚',
  ', AY':'南极洲',', AQ':'南极洲',
  ', WZ':'斯威士兰',', SW':'瑞典',
}

export function stationCN(name) {
  if (!name) return ''
  // 精确匹配
  if (STATION_CN[name]) return STATION_CN[name]
  // 尝试模糊匹配：去掉尾部空格
  const trimmed = name.trim()
  if (STATION_CN[trimmed]) return STATION_CN[trimmed]
  // 替换国家代码后缀
  let result = trimmed
  for (const [code, cn] of Object.entries(COUNTRY_CN)) {
    if (result.endsWith(code)) {
      result = result.slice(0, -code.length) + ', ' + cn
      break
    }
  }
  return result
}
