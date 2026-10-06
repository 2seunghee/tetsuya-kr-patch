You are doing a THIRD-PASS quality check of the Korean fan-translation of the GBA game "Gambler Densetsu Tetsuya: Yomigaeru Densetsu". Two passes already fixed terminology; your job now is to read like a native Korean player and catch what is still AWKWARD, UNNATURAL, MISTRANSLATED, or INCONSISTENT. Report findings; do not rewrite entries that are fine.

PROJECT ROOT: C:\Users\Administrator\Documents\Gambler Densetsu Tetsuya - Yomigaeru Densetsu (Japan)

1. Read assets\translation\glossary.md sections 1, 3, 5, 7 (names, mahjong terms, stock lines, style guide) and the FIXED DECISIONS below (they override the glossary where they differ).
2. Your range: assets\translation\segments\{SEGFILE}, entries from id {FIRST} through {LAST} inclusive ({COUNT} entries). Each entry has "source" (Japanese with <TOKENS>) and "target" (current Korean). Read them with Python (set PYTHONIOENCODING=utf-8). Read the whole range in order first so you know the scene, speakers and context; entries are consecutive dialogue. Speaker is implied by <FACE:xx>/<PORTL/PORTR:xx..> and carries over to following entries until changed (FACE 00/01=테쯔야, 05/15/1e=보슈, 0b/12=단치, 0c=인나미, 0d=신, 09/0a=토쿠조 콤비, 07/08=쌍둥이, 06=토비, 19/1a=점장, 10/11=네즈 부부, 13=빡빡머리, 14=유우, 18=마담, 16=나카, 1d=단치 아버지, 0f=미국물 든 사내, 20=종이 브로커). Lines in 『』 without a face are field/vendor/sign lines; lines in （） are inner monologue.
3. Output: work\review2\findings_{OUTNAME}.json — a JSON LIST of objects {"id": "...", "kind": "awkward|meaning|term|register|typo|layout", "why": "<one short Korean sentence>", "current": "<exact current target>", "proposed": "<full replacement target>"}. Only include entries you would actually change. "proposed" must be the complete target string (all tokens included).

What to look for (in priority order):
(a) Mistranslation or dropped/added meaning versus the Japanese; wrong subject/object; wrong speaker intent; idioms translated literally.
(b) Translationese and unnatural Korean: Japanese sentence rhythm, odd particles, 「~것이다」 overuse, literal 「~해 주다」 chains, unnatural interjections, wordy phrasing that a Korean 1940s gambler-drama script would not use. Dialogue must sound like spoken Korean of that character.
(c) Register/voice inconsistency within the scene and against the speaker table (Tetsuya rough 반말 to everyone; Danchi light ~슴다/~요 to Tetsuya, 반말 to others; Boshu laid-back 반말; vendors 장사꾼 존대; Nezu couple polite before the reveal then sneering 반말; old man 하게체).
(d) Terminology deviating from FIXED DECISIONS, or the same thing named two ways within your range.
(e) Spelling/spacing (한글 맞춤법·띄어쓰기), punctuation misuse, a word split across the line break when a cleaner split exists within the 18-cell limit.

FIXED DECISIONS (apply everywhere):
- Names: 哲也→테쯔야, 哲→테쯔 (never 테츠). 房州→보슈, 房州さん→보슈 씨. ダンチ→단치. 印南→인나미. ユウ→유우, ユウさん→유우 씨. トビさん→토비 씨. 徳三→토쿠조, 徳さん→토쿠 씨. リサ→리사. コロ→코로. ママ→마담. マスター→마스터. 店長→점장. 店主→점주. 根津→네즈. 中→나카. 坊や→꼬마, 坊や哲→꼬마 테쯔. 小僧 / child 坊主→꼬맹이; 坊主頭→빡빡머리. 哲さん said by 단치→테쯔 형님, by others→테쯔 씨. 兄貴 (twins)→형님. 親父 = one's own father→아버지; 親父 = shopkeeper/old man→영감 or 아저씨 by tone.
- Gambler terms: 玄人→바이닌 (never 타짜/바이닝/프로 unless source says プロ), トーシロ→초짜, ハンチク→얼치기, イカサマ→이카사마 (never 속임수; インチキ may be 속임수), 積み込み→패 쌓기, 元禄積み→겐로쿠 쌓기, 通し/通しサイン→통신/통신 사인, 【通し】→【통신】, 左手芸→왼손 기술, 【左手芸】→【왼손 기술】, ツバメ返し→제비뒤집기, 握り込み→패 감추기, ギる→감추다, ギリ師→감추기꾼, オヒキ→오히키, エレベーター→엘리베이터, ガン牌→간패, 匹→필, タネ(銭)→밑천, 雀荘→작장, 卓→탁, 流れ→흐름, ツキ→끗발, 二の二の天和→2의 2 천화, カモ→호구, ダンナ→물주, 勝ち逃げ→먹튀, かっぱぐ→털다, 場代→자릿세, 玄人文庫→『바이닌 문고(상/중)』을 / 『바이닌 문고(하)』를, アガる→화료하다.
- Mahjong: ツモ→쯔모, ロン→론, リーチ/立直→리치, テンパイ→텐파이, 満貫→만관, 跳満→하네만, 倍満→배만, 三倍満→삼배만, 役満→역만, 国士無双→국사무쌍, 大三元→대삼원, 四暗刻→사암각, 九連宝燈→구련보등, 天和→천화, 配牌→배패, 捨て牌→버림패, 当たり牌→당첨패, 振り込む→쏘다, 放銃→방총, 降りる→내리다, 鳴く→울다, ポン→퐁, オーラス→올라스, 親→오야 (親の倍満→오야 배만), 子→자, 原点→원점, トップ→톱, 待ち→대기, 高目/安目→비싼 쪽/싼 쪽, ドラ→도라, 萬子/索子/筒子→만수/삭수/통수, 一萬→1만 (digits), 山→패산, ツモ巡→쯔모 순, 半荘→반장, 東一局→동1국, 満卓→만탁.
- Era words: 昭和二十一年→쇼와 21년, 戦後→전후, 焼け跡→폐허, バクダン→바쿠단, カストリ→카스토리, 牛めし→규메시, 賽銭箱→새전함, 米軍払い下げ→미군 불하품, 新宿→신주쿠, 浅草→아사쿠사, 上野→우에노, 房総→보소, 千葉→치바.
- Speech levels: Tetsuya rough 반말 (호칭 보슈 씨). Boshu laid-back 반말, calls Tetsuya 꼬마. Danchi to Tetsuya: light polite with っス contractions (~슴다/~임다/~함다/~요/~죠) — never formal ~습니다; Danchi to others: 반말. Innami eerie 반말 with 쿠쿠쿠. Nezu couple: fake 존댓말 before the reveal, sneering 반말 after. Mama: casual female 반말. Twins to Tetsuya: light period 존댓말. Vendors/NPC per glossary §5.
- Punctuation: keep 「」『』（）【】 exactly as the source; one-character … ; ASCII , . ! ? ; ⁉ allowed; 『깡통・병 버리지 말 것』 with ・; 「{L} 버튼」 with a space; no Japanese characters outside tokens.

HARD RULES for every "proposed" (validator): keep every <TOKEN> exactly and in order; keep {BLKn}/{A}/{L}... tokens; same terminator (<END>/<NEXT>); max 2 lines per page (split at <PAGE>/<PAGE2>/<CLR>), max 18 cells per line (1 Hangul/punct/space/digit/{TOKEN} = 1 cell; 「」『』（）【】 count 1 each); choice lines: option 1 after one leading space, option 2 starting at column index 9. Do not change 「………」「・・・・・」 lengths.

Validate your file before finishing (PYTHONIOENCODING=utf-8), run from PROJECT ROOT. Put this in a file work\review2\check_{OUTNAME}.py and run it:

    import json,sys
    sys.path.insert(0,'tools')
    from validate_translation import check_entry
    from textcodec import load_glyph_table
    from bdffont import BdfFont
    f=BdfFont('assets/fonts/sources/galmuri/Galmuri11.bdf'); _,t=load_glyph_table()
    seg={e['id']:e for e in json.load(open('assets/translation/segments/{SEGFILE}',encoding='utf-8'))['entries']}
    d=json.load(open('work/review2/findings_{OUTNAME}.json',encoding='utf-8')); bad=0
    for x in d:
        e=seg[x['id']]
        if x['current']!=e['target']: bad+=1; print(x['id'],'current mismatch')
        if x['proposed']==e['target']: bad+=1; print(x['id'],'no change')
        errs=check_entry(dict(e,target=x['proposed']),f,t)
        if errs: bad+=1; print(x['id'],errs)
    print('findings',len(d),'bad',bad)

Fix until bad == 0. Be thorough but honest: a typical range of this size has maybe 5-25 real findings. Do not edit segment files, glossary, or drafts. Final report (short): number of findings by kind, and any judgment call you were unsure about (id + one line).
