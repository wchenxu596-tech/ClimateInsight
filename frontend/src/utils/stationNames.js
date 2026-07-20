const STATION_CN = {
  'AMUNDSEN SCOTT, AY':'阿蒙森-斯科特站', 'ARAFAT, SA':'阿拉法特',
  'VOSTOK, AY':'东方站', 'SITEKI, WZ':'锡泰基', 'CONCORDIA, AQ':'康科迪亚站',
  'DOME C II, AQ':'冰穹C二号', 'MARBLE POINT, AY':'大理石角',
  'MAHABALESHWAR, IN':'默哈伯莱什沃尔', 'HONAVAR, IN':'霍纳瓦尔',
  'JOKKMOKK FPL, SW':'约克莫克', 'HALLEY, AY':'哈雷站',
  'KHLONG YAI, TH':'空艾', 'KAYES DAG DAG, ML':'卡伊',
  'MINA, SA':'米纳', 'KOSRAE INTERNATIONAL AIRPORT, FM FM':'科斯雷机场',
  'MATAM OURO SOGUI, SG':'马塔姆', 'PREAH VIHEAR, CB':'柏威夏',
  'PODOR, SG':'波多尔', 'NARA KEIBANE, ML':'纳拉',
  'YELIMANE, ML':'耶利马内', 'LINGUERE, SG':'林盖尔',
  'TAMBACOUNDA, SG':'坦巴昆达', 'TILLABERY, NG':'蒂拉贝里',
  'NIORO DU SAHEL, ML':'纽罗', 'BERNARD HARBOUR, CA':'伯纳德港',
  'COLVILLE LAKE NWT, CA':'科尔维尔湖', 'DAWEI, BM':'土瓦',
  'YE, BM':'耶', 'MAO, CD':'马奥', 'ZAKATALA, AJ':'扎卡塔拉',
  'GAVAR, AM':'加瓦尔', 'FAHUD AUT, MU':'法胡德',
  'BALDRICK AWS, AY':'鲍德里克站', 'CAPE PHILLIPS, AY':'菲利普斯角',
  'DOME PLATEAU DOME A, AY':'冰穹A', 'DOME PLATEAU EAGLE, AY':'冰穹鹰',
  'HALVFARRYGGEN EP11, AY':'半脊EP11', 'LAW DOME SUMMIT, AY':'劳穹顶',
  'MID POINT, AY':'中点站', 'PRIESTLEY GLACIER, AY':'普里斯特利冰川',
  'S.A.N.A.E. AWS, AY':'南非科考站', 'UNIVERSITY WI ID 8917 SKI BLU, AY':'威大8917站',
  'UNIVERSITY WI ID 8925 LIMBERT AWS, AY':'威大8925站',
  'HALIM PERDANAKUSUMA INTERNATIONAL, ID':'哈利姆机场',
  'KOKONAO TIMUKA, ID':'科科纳奥', 'SAM RATULANGI, ID':'萨姆拉图兰吉',
  'SANTO PEKOA INTERNATIONAL, NH':'桑托佩可亚', 'OSMANY INTERNATIONAL, BG':'奥斯曼尼机场',
  'MILFORD SOUNDN AWS, NZ':'米尔福德峡湾', 'SECRETARY ISLAND AWS, NZ':'秘书岛',
}

export function stationCN(name) {
  return STATION_CN[name] || name
}
