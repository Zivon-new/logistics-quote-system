-- ============================================================
-- add_more_ports.sql
-- 扩充全球港口数据：32 → 125+ 条
-- 日期: 2026-03-17
-- ============================================================
USE `price_test_v2`;

INSERT INTO ports
  (UNLOCODE, 港口名称, 港口英文名, 国家代码, 国家名称, 城市,
   纬度, 经度, 港口类型, 所属时区, 平均清关天数, LPI风险等级, 备注)
VALUES

-- ===== 中国（新增） =====
('CNTSN', '天津港',         'Tianjin Port',                   'CN','中国',    '天津',        38.9918, 117.7226, '海港',  'Asia/Shanghai',      2.0, '低', '中国北方最大综合性港口'),
('CNDLC', '大连港',         'Dalian Port',                    'CN','中国',    '大连',        38.9140, 121.6366, '海港',  'Asia/Shanghai',      1.5, '低', '东北地区重要出海口'),
('CNXMN', '厦门港',         'Xiamen Port',                    'CN','中国',    '厦门',        24.4798, 118.0808, '海港',  'Asia/Shanghai',      1.5, '低', '对台海运重要口岸'),
('CNFOC', '福州港',         'Fuzhou Port',                    'CN','中国',    '福州',        25.7180, 119.6308, '海港',  'Asia/Shanghai',      2.0, '低', NULL),
('CNLYG', '连云港',         'Lianyungang Port',               'CN','中国',    '连云港',      34.7200, 119.4400, '海港',  'Asia/Shanghai',      2.0, '低', '新亚欧大陆桥东端起点'),
('CNTAC', '太仓港',         'Taicang Port',                   'CN','中国',    '太仓',        31.5000, 121.0833, '海港',  'Asia/Shanghai',      1.5, '低', NULL),
('CNPVG', '上海浦东机场',   'Shanghai Pudong Airport',        'CN','中国',    '上海',        31.1443, 121.8083, '空港',  'Asia/Shanghai',      1.0, '低', '中国最大国际空运枢纽'),
('CNSZB', '深圳宝安机场',   'Shenzhen Bao\'an Airport',       'CN','中国',    '深圳',        22.6394, 113.8108, '空港',  'Asia/Shanghai',      1.0, '低', NULL),
('CNCTU', '成都天府机场',   'Chengdu Tianfu Airport',         'CN','中国',    '成都',        30.3125, 104.4442, '空港',  'Asia/Shanghai',      1.5, '低', NULL),
('CNWUH', '武汉阳逻港',     'Wuhan Yangluo Port',             'CN','中国',    '武汉',        30.5830, 114.5700, '内陆港','Asia/Shanghai',      2.0, '低', '长江中游重要内河港'),
('CNCKG', '重庆果园港',     'Chongqing Guoyuan Port',         'CN','中国',    '重庆',        29.6500, 106.6100, '内陆港','Asia/Shanghai',      2.5, '低', '中欧班列西部枢纽'),
('CNXIA', '西安国际港',     'Xi\'an International Port',      'CN','中国',    '西安',        34.3416, 108.9398, '铁路港','Asia/Shanghai',      2.0, '低', '中欧班列重要节点'),

-- ===== 日本（新增） =====
('JPYOK', '横滨港',         'Port of Yokohama',               'JP','日本',    '横滨',        35.4500, 139.6500, '海港',  'Asia/Tokyo',         1.5, '低', NULL),
('JPNGO', '名古屋港',       'Port of Nagoya',                 'JP','日本',    '名古屋',      35.0500, 136.8833, '海港',  'Asia/Tokyo',         1.5, '低', '日本最大贸易港口'),
('JPUKB', '神户港',         'Port of Kobe',                   'JP','日本',    '神户',        34.6833, 135.2000, '海港',  'Asia/Tokyo',         1.5, '低', NULL),
('JPNRT', '东京成田机场',   'Tokyo Narita Airport',           'JP','日本',    '千叶',        35.7647, 140.3864, '空港',  'Asia/Tokyo',         1.0, '低', NULL),
('JPKIX', '大阪关西机场',   'Kansai International Airport',   'JP','日本',    '大阪',        34.4347, 135.2440, '空港',  'Asia/Tokyo',         1.0, '低', NULL),

-- ===== 韩国（新增） =====
('KRICN', '仁川机场',       'Incheon International Airport',  'KR','韩国',    '仁川',        37.4602, 126.4407, '空港',  'Asia/Seoul',         1.0, '低', '亚洲重要转运机场'),
('KRINC', '仁川港',         'Port of Incheon',                'KR','韩国',    '仁川',        37.4500, 126.6167, '海港',  'Asia/Seoul',         1.5, '低', NULL),
('KRKTC', '光阳港',         'Port of Gwangyang',              'KR','韩国',    '光阳',        34.9000, 127.6833, '海港',  'Asia/Seoul',         2.0, '低', NULL),

-- ===== 台湾 =====
('TWKHH', '高雄港',         'Port of Kaohsiung',              'TW','台湾',    '高雄',        22.6167, 120.3000, '海港',  'Asia/Taipei',        2.0, '中', '台湾最大港口，两岸直航重要节点'),
('TWTPE', '台北桃园机场',   'Taoyuan International Airport',  'TW','台湾',    '桃园',        25.0777, 121.2327, '空港',  'Asia/Taipei',        1.5, '中', NULL),

-- ===== 新加坡（新增） =====
('SGCHA', '樟宜机场',       'Singapore Changi Airport',       'SG','新加坡',  '新加坡',       1.3644, 103.9915, '空港',  'Asia/Singapore',     0.5, '低', '连续多年全球最佳机场'),

-- ===== 马来西亚（新增） =====
('MYPKG', '巴生港',         'Port Klang',                     'MY','马来西亚', '巴生',         3.0000, 101.4000, '海港',  'Asia/Kuala_Lumpur',  3.0, '中', '马来西亚最大港口'),
('MYTPP', '丹戎柏勒巴斯港', 'Port of Tanjung Pelepas',        'MY','马来西亚', '柔佛',         1.3600, 103.5500, '海港',  'Asia/Kuala_Lumpur',  2.5, '中', NULL),
('MYKUL', '吉隆坡国际机场', 'Kuala Lumpur Intl Airport',      'MY','马来西亚', '吉隆坡',       2.7456, 101.7099, '空港',  'Asia/Kuala_Lumpur',  1.5, '中', NULL),

-- ===== 泰国 =====
('THLCH', '林查班港',       'Laem Chabang Port',              'TH','泰国',    '春武里',      13.0843, 100.8897, '海港',  'Asia/Bangkok',       3.5, '中', '泰国最大深水港'),
('THBKK', '曼谷素万那普机场','Bangkok Suvarnabhumi Airport',  'TH','泰国',    '曼谷',        13.6900, 100.7501, '空港',  'Asia/Bangkok',       2.0, '中', NULL),

-- ===== 越南（新增） =====
('VNHPH', '海防港',         'Hai Phong Port',                 'VN','越南',    '海防',        20.8449, 106.6881, '海港',  'Asia/Ho_Chi_Minh',   4.0, '中', NULL),

-- ===== 印度尼西亚 =====
('IDJKT', '丹戎不碌港',     'Tanjung Priok Port',             'ID','印度尼西亚','雅加达',     -6.1000, 106.8667, '海港',  'Asia/Jakarta',       4.5, '中', '印尼最大港口'),
('IDSUB', '泗水港',         'Tanjung Perak Port',             'ID','印度尼西亚','泗水',       -7.2458, 112.7378, '海港',  'Asia/Jakarta',       4.0, '中', NULL),
('IDCGK', '雅加达苏加诺哈达机场','Jakarta Soekarno-Hatta Airport','ID','印度尼西亚','雅加达', -6.1256, 106.6559, '空港',  'Asia/Jakarta',       2.0, '中', NULL),

-- ===== 菲律宾（新增） =====
('PHCEB', '宿务港',         'Port of Cebu',                   'PH','菲律宾',  '宿务',        10.3154, 123.8990, '海港',  'Asia/Manila',        5.0, '中', NULL),

-- ===== 缅甸 =====
('MMRGN', '仰光港',         'Port of Yangon',                 'MM','缅甸',    '仰光',        16.7833, 96.1667, '海港',  'Asia/Rangoon',       8.0, '中', '军事政变后清关效率下降'),

-- ===== 孟加拉国 =====
('BDCGP', '吉大港',         'Port of Chittagong',             'BD','孟加拉国','吉大港',      22.3384, 91.8317, '海港',  'Asia/Dhaka',         7.0, '中', '孟加拉国最大港口，长期拥堵'),

-- ===== 柬埔寨 =====
('KHPNH', '金边港',         'Port of Phnom Penh',             'KH','柬埔寨',  '金边',        11.5564, 104.9282, '内陆港','Asia/Phnom_Penh',    5.0, '中', NULL),

-- ===== 斯里兰卡 =====
('LKCMB', '科伦坡港',       'Port of Colombo',                'LK','斯里兰卡','科伦坡',       6.9271,  79.8612, '海港',  'Asia/Colombo',       4.0, '中', '南亚重要转运港'),

-- ===== 印度 =====
('INBOM', '孟买/JNPT港',    'Jawaharlal Nehru Port',          'IN','印度',    '孟买',        18.9480,  72.9517, '海港',  'Asia/Kolkata',       5.0, '中', '印度最大集装箱港口'),
('INMAA', '钦奈港',         'Chennai Port',                   'IN','印度',    '钦奈',        13.0827,  80.2987, '海港',  'Asia/Kolkata',       5.5, '中', NULL),
('INMUN', '孟德拉港',       'Mundra Port',                    'IN','印度',    '孟德拉',      22.8390,  69.7046, '海港',  'Asia/Kolkata',       5.0, '中', '印度最大私营港口'),
('INBOI', '孟买机场',       'Mumbai Chhatrapati Shivaji Airport','IN','印度', '孟买',        19.0896,  72.8656, '空港',  'Asia/Kolkata',       2.5, '中', NULL),

-- ===== 巴基斯坦 =====
('PKKAR', '卡拉奇港',       'Port of Karachi',                'PK','巴基斯坦','卡拉奇',      24.8607,  66.9900, '海港',  'Asia/Karachi',       7.0, '高', '清关复杂，外汇危机影响进口'),

-- ===== 阿联酋（新增） =====
('AEJEA', '杰贝阿里港',     'Port of Jebel Ali',              'AE','阿联酋',  '迪拜',        25.0076,  55.1354, '海港',  'Asia/Dubai',         2.0, '中', '中东最大集装箱港，全球前10，霍尔木兹扼守点'),
('AEAUH', '阿布扎比哈利法港','Abu Dhabi Khalifa Port',        'AE','阿联酋',  '阿布扎比',    24.8029,  54.6500, '海港',  'Asia/Dubai',         2.5, '中', NULL),
('AEDBA', '迪拜国际机场',   'Dubai International Airport',    'AE','阿联酋',  '迪拜',        25.2532,  55.3657, '空港',  'Asia/Dubai',         1.5, '中', '全球最繁忙国际机场之一'),

-- ===== 沙特（新增） =====
('SAKAB', '阿卜杜拉国王港', 'King Abdullah Port',             'SA','沙特',    '吉达',        22.4000,  39.1167, '海港',  'Asia/Riyadh',        3.5, '中', '红海重要港口，清关周期长'),
('SARUH', '利雅得机场',     'Riyadh King Khalid Airport',     'SA','沙特',    '利雅得',      24.9578,  46.6989, '空港',  'Asia/Riyadh',        2.0, '中', NULL),

-- ===== 卡塔尔 =====
('QAHMD', '哈马德港',       'Hamad Port',                     'QA','卡塔尔',  '多哈',        24.9333,  51.5667, '海港',  'Asia/Qatar',         2.5, '中', NULL),
('QADOH', '多哈哈马德机场', 'Doha Hamad Intl Airport',        'QA','卡塔尔',  '多哈',        25.2609,  51.6138, '空港',  'Asia/Qatar',         1.5, '中', NULL),

-- ===== 科威特 =====
('KWKWI', '科威特舒韦赫港', 'Shuwaikh Port',                  'KW','科威特',  '科威特城',    29.3600,  47.9700, '海港',  'Asia/Kuwait',        5.0, '中', '政局影响清关效率'),

-- ===== 阿曼 =====
('OMSOH', '索哈尔港',       'Port of Sohar',                  'OM','阿曼',    '索哈尔',      24.3667,  56.7833, '海港',  'Asia/Muscat',        3.0, '中', '霍尔木兹过境风险，本国相对中立'),

-- ===== 以色列 =====
('ILHFA', '海法港',         'Port of Haifa',                  'IL','以色列',  '海法',        32.8192,  35.0000, '海港',  'Asia/Jerusalem',     4.0, '中', '多线战争背景下港口运营受限'),

-- ===== 土耳其 =====
('TRAMB', '阿姆巴利港',     'Ambarli Container Port',         'TR','土耳其',  '伊斯坦布尔',  40.9758,  28.6876, '海港',  'Europe/Istanbul',    4.0, '中', '欧亚连接重要港口'),
('TRMER', '梅尔辛港',       'Port of Mersin',                 'TR','土耳其',  '梅尔辛',      36.7987,  34.6314, '海港',  'Europe/Istanbul',    4.5, '中', NULL),

-- ===== 埃及 =====
('EGPSD', '塞得港',         'Port Said',                      'EG','埃及',    '塞得港',      31.2565,  32.2841, '海港',  'Africa/Cairo',       3.0, '中', '苏伊士运河北端，过境量下降'),
('EGALX', '亚历山大港',     'Port of Alexandria',             'EG','埃及',    '亚历山大',    31.2001,  29.9187, '海港',  'Africa/Cairo',       4.0, '中', '埃及最大港口'),

-- ===== 荷兰（新增） =====
('NLAMS', '阿姆斯特丹机场', 'Amsterdam Schiphol Airport',     'NL','荷兰',    '阿姆斯特丹',  52.3086,   4.7639, '空港',  'Europe/Amsterdam',   1.0, '低', NULL),

-- ===== 比利时 =====
('BEANR', '安特卫普港',     'Port of Antwerp',                'BE','比利时',  '安特卫普',    51.2194,   4.4025, '海港',  'Europe/Brussels',    2.0, '低', '欧洲第二大港，化工品重要中心'),

-- ===== 法国 =====
('FRLEH', '勒阿弗尔港',     'Port of Le Havre',               'FR','法国',    '勒阿弗尔',    49.4800,   0.1100, '海港',  'Europe/Paris',       2.5, '低', '法国最大港口'),
('FRCDG', '巴黎戴高乐机场', 'Paris CDG Airport',              'FR','法国',    '巴黎',        49.0097,   2.5479, '空港',  'Europe/Paris',       1.5, '低', NULL),

-- ===== 意大利 =====
('ITGOA', '热那亚港',       'Port of Genoa',                  'IT','意大利',  '热那亚',      44.4074,   8.9340, '海港',  'Europe/Rome',        3.0, '低', '意大利最大港口'),
('ITMXP', '米兰马尔彭萨机场','Milan Malpensa Airport',        'IT','意大利',  '米兰',        45.6306,   8.7231, '空港',  'Europe/Rome',        1.5, '低', NULL),

-- ===== 希腊 =====
('GRPIR', '比雷埃夫斯港',   'Port of Piraeus',                'GR','希腊',    '比雷埃夫斯',  37.9500,  23.6200, '海港',  'Europe/Athens',      3.5, '低', '地中海重要转运港，中远集团运营'),

-- ===== 葡萄牙 =====
('PTSIE', '锡尼什港',       'Port of Sines',                  'PT','葡萄牙',  '锡尼什',      37.9500,  -8.8800, '海港',  'Europe/Lisbon',      2.0, '低', '欧洲大西洋航线重要深水港'),

-- ===== 波兰 =====
('PLGDY', '格但斯克港',     'Port of Gdansk',                 'PL','波兰',    '格但斯克',    54.3520,  18.6466, '海港',  'Europe/Warsaw',      3.0, '低', '波罗的海重要港口'),

-- ===== 瑞典 =====
('SEGOT', '哥德堡港',       'Port of Gothenburg',             'SE','瑞典',    '哥德堡',      57.7089,  11.9746, '海港',  'Europe/Stockholm',   2.5, '低', '北欧最大港口'),

-- ===== 芬兰 =====
('FIHEL', '赫尔辛基港',     'Port of Helsinki',               'FI','芬兰',    '赫尔辛基',    60.1699,  24.9384, '海港',  'Europe/Helsinki',    2.5, '低', NULL),

-- ===== 俄罗斯 =====
('RULED', '圣彼得堡港',     'Port of St. Petersburg',         'RU','俄罗斯',  '圣彼得堡',    59.9311,  30.3609, '海港',  'Europe/Moscow',      6.0, '高', '欧美制裁，贸易受严重限制'),
('RUVVO', '符拉迪沃斯托克港','Port of Vladivostok',           'RU','俄罗斯',  '符拉迪沃斯托克',43.1155, 131.8823,'海港','Asia/Vladivostok',   6.0, '高', '远东出海口，对中贸易通道'),

-- ===== 美国（新增） =====
('USNYC', '纽约/纽瓦克港',  'Port of New York/New Jersey',    'US','美国',    '纽约',        40.6892, -74.0445, '海港',  'America/New_York',   3.0, '低', '美国东海岸最大港口'),
('USSAV', '萨凡纳港',       'Port of Savannah',               'US','美国',    '萨凡纳',      32.0809, -81.0912, '海港',  'America/New_York',   2.5, '低', '美国东南部增长最快港口'),
('USHOU', '休斯顿港',       'Port of Houston',                'US','美国',    '休斯顿',      29.7604, -95.3698, '海港',  'America/Chicago',    3.0, '低', '美国能源出口重要港口'),
('USSEA', '西雅图港',       'Port of Seattle',                'US','美国',    '西雅图',      47.6062,-122.3321, '海港',  'America/Los_Angeles',2.5, '低', NULL),
('USJFK', '纽约肯尼迪机场', 'John F. Kennedy Airport',        'US','美国',    '纽约',        40.6413, -73.7781, '空港',  'America/New_York',   2.0, '低', NULL),
('USORD', '芝加哥奥黑尔机场','Chicago O\'Hare Intl Airport',  'US','美国',    '芝加哥',      41.9742, -87.9073, '空港',  'America/Chicago',    2.0, '低', '美国重要航空货运枢纽'),
('USANC', '安克雷奇机场',   'Ted Stevens Anchorage Airport',  'US','美国',    '安克雷奇',    61.1744,-149.9964, '空港',  'America/Anchorage',  1.5, '低', '亚欧北美空运中转枢纽'),

-- ===== 加拿大 =====
('CAVAN', '温哥华港',       'Port of Vancouver',              'CA','加拿大',  '温哥华',      49.2827,-123.1207, '海港',  'America/Vancouver',  2.5, '低', '加拿大最大港口'),
('CAMTR', '蒙特利尔港',     'Port of Montreal',               'CA','加拿大',  '蒙特利尔',    45.5017, -73.5673, '海港',  'America/Toronto',    3.0, '低', NULL),

-- ===== 墨西哥 =====
('MXZLO', '曼萨尼略港',     'Port of Manzanillo',             'MX','墨西哥',  '曼萨尼略',    19.0500,-104.3167, '海港',  'America/Mazatlan',   4.0, '中', '墨西哥太平洋最大港口'),
('MXVRA', '韦拉克鲁斯港',   'Port of Veracruz',               'MX','墨西哥',  '韦拉克鲁斯',  19.2000, -96.1333, '海港',  'America/Mexico_City',4.5, '中', NULL),

-- ===== 巴拿马 =====
('PABLB', '巴拿马巴尔博亚港','Port of Balboa',                'PA','巴拿马',  '巴拿马城',     8.9667, -79.5667, '海港',  'America/Panama',     3.5, '中', '巴拿马运河太平洋端枢纽'),
('PACTB', '科隆港',         'Port of Colon',                  'PA','巴拿马',  '科隆',         9.3547, -79.9007, '海港',  'America/Panama',     3.5, '中', '巴拿马运河大西洋端，自由贸易区'),

-- ===== 哥伦比亚 =====
('COBUN', '布埃纳文图拉港', 'Port of Buenaventura',           'CO','哥伦比亚','布埃纳文图拉',  3.8800, -77.0300, '海港',  'America/Bogota',     5.0, '中', '哥伦比亚太平洋最大港口'),

-- ===== 巴西 =====
('BRSSZ', '桑托斯港',       'Port of Santos',                 'BR','巴西',    '桑托斯',     -23.9535, -46.3342, '海港',  'America/Sao_Paulo',  6.0, '中', '南美最大港口'),
('BRRIG', '里约热内卢港',   'Port of Rio de Janeiro',         'BR','巴西',    '里约热内卢', -22.9068, -43.1729, '海港',  'America/Sao_Paulo',  6.5, '中', NULL),

-- ===== 阿根廷 =====
('ARBUE', '布宜诺斯艾利斯港','Port of Buenos Aires',          'AR','阿根廷',  '布宜诺斯艾利斯',-34.6037,-58.3816,'海港','America/Argentina/Buenos_Aires',7.0,'中',NULL),

-- ===== 秘鲁 =====
('PECLL', '卡亚俄港',       'Port of Callao',                 'PE','秘鲁',    '卡亚俄',     -12.0500, -77.1333, '海港',  'America/Lima',       5.0, '中', '秘鲁最大港口'),

-- ===== 智利 =====
('CLSAI', '圣安东尼奥港',   'Port of San Antonio',            'CL','智利',    '圣安东尼奥', -33.5935, -71.6135, '海港',  'America/Santiago',   4.5, '中', '智利最大集装箱港'),

-- ===== 摩洛哥 =====
('MATAN', '丹吉尔地中海港', 'Tanger Med Port',                'MA','摩洛哥',  '丹吉尔',      35.8833,  -5.5000, '海港',  'Africa/Casablanca',  3.0, '中', '非洲最大集装箱港，地中海重要枢纽'),
('MACAS', '卡萨布兰卡港',   'Port of Casablanca',             'MA','摩洛哥',  '卡萨布兰卡',  33.5731,  -7.5898, '海港',  'Africa/Casablanca',  4.0, '中', NULL),

-- ===== 南非 =====
('ZADUR', '德班港',         'Port of Durban',                 'ZA','南非',    '德班',       -29.8587,  31.0218, '海港',  'Africa/Johannesburg',4.0, '中', '非洲最繁忙港口，运营效率持续偏低'),
('ZACPT', '开普敦港',       'Port of Cape Town',              'ZA','南非',    '开普敦',     -33.9249,  18.4241, '海港',  'Africa/Johannesburg',4.5, '中', NULL),

-- ===== 肯尼亚 =====
('KEMBA', '蒙巴萨港',       'Port of Mombasa',                'KE','肯尼亚',  '蒙巴萨',      -4.0500,  39.6667, '海港',  'Africa/Nairobi',     6.0, '高', '东非最大港口'),

-- ===== 坦桑尼亚 =====
('TZDAR', '达累斯萨拉姆港', 'Port of Dar es Salaam',          'TZ','坦桑尼亚','达累斯萨拉姆', -6.8000,  39.2833, '海港',  'Africa/Dar_es_Salaam',7.0,'高', NULL),

-- ===== 尼日利亚 =====
('NGAPP', '阿帕帕港（拉各斯）','Apapa Port Lagos',            'NG','尼日利亚','拉各斯',       6.4531,   3.3958, '海港',  'Africa/Lagos',       9.0, '高', '西非最大港口，清关极为复杂'),

-- ===== 埃塞俄比亚 =====
('ETADD', '亚的斯亚贝巴机场','Addis Ababa Bole Intl Airport', 'ET','埃塞俄比亚','亚的斯亚贝巴', 8.9779, 38.7993,'空港',  'Africa/Addis_Ababa', 3.0, '中', '非洲航空枢纽，东非腹地内陆国门户'),

-- ===== 澳大利亚（新增） =====
('AUBNE', '布里斯班港',     'Port of Brisbane',               'AU','澳大利亚','布里斯班',   -27.4698, 153.0251, '海港',  'Australia/Brisbane', 3.0, '低', NULL),
('AUFRE', '弗里曼特尔港',   'Port of Fremantle',              'AU','澳大利亚','珀斯',        -32.0569, 115.7439, '海港',  'Australia/Perth',    3.5, '低', NULL),
('AUADL', '阿德莱德港',     'Port of Adelaide',               'AU','澳大利亚','阿德莱德',   -34.9285, 138.6007, '海港',  'Australia/Adelaide', 3.5, '低', NULL),
('AUSYA', '悉尼金斯福德机场','Sydney Kingsford Smith Airport','AU','澳大利亚','悉尼',        -33.9399, 151.1753, '空港',  'Australia/Sydney',   1.5, '低', NULL),

-- ===== 新西兰 =====
('NZAKL', '奥克兰港',       'Port of Auckland',               'NZ','新西兰',  '奥克兰',     -36.8485, 174.7633, '海港',  'Pacific/Auckland',   3.0, '低', NULL);
