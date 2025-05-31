import json
import csv
import os
import re
ALL_TRANSLATABLE_FIELDS = ["strName", "strDesc", "strNameFriendly", "strNameShort", "strTitle", "strTooltip"]

# ====================================================================================================================================
# === 사용자 설정 ===
# 스크립트의 동작 방식을 여기서 설정합니다.

# 작동방식
# strTitle, strDesc, strName 등의 필드는 대부분이 동일하므로 해당 필드의 원문 값을 CSV와 JSON 영어 값을 비교한뒤 둘이 완벽히 일치할 경우
# CSV 한국어 번역본 값을 영문 JSON 의 필드값에 치환해 넣어 output 폴더로 출력합니다.

# ====================================================================================================================================

# 1. CSV 파일 경로 설정 (기본값 또는 매칭되는 CSV가 없을 때 사용)
# JSON 파일 내 텍스트를 번역할 때 사용할 기본 CSV 파일의 경로를 지정합니다.
# 'match_csv_by_json_filename'이 True일 때, 매칭되는 CSV가 없으면 이 파일을 사용합니다.
# 3번에서 매칭되는 CSV가 없을 경우 사용하므로 폴더가 아닌 단일 파일을 지정해야 합니다
csv_file_path = './CSV/' # 예: 'C:/Users/YourUser/Desktop/translations.csv' 또는 './data/translations.csv'

# 2. JSON 파일 처리 방식 설정
# True: json_input_directory에 지정된 디렉터리 내 모든 JSON 파일을 재귀적으로 처리합니다.
# False: json_single_file_name에 지정된 단일 JSON 파일만 처리합니다.
process_all_files_in_directory = True 

# 3. JSON 입력 경로 설정 (process_all_files_in_directory 설정에 따라 사용)
# process_all_files_in_directory가 True일 때: JSON 파일들이 위치한 디렉터리 경로. 하위 폴더도 탐색합니다.
# 수정되지 않은 영어 JSON 원문이 위치한 폴더를 지정해야 합니다
# CSV에서 매치되는 번역문이 적용되고 Output에 출력되기 위한 파일입니다
json_input_directory = './EN_json/' # 예: 'C:/Users/YourUser/Documents/my_json_data/' 또는 './input_data/'

# process_all_files_in_directory가 False일 때: 처리할 단일 JSON 파일의 경로.
# 2가 *** True *** 일 경우 무시해도 됩니다.
json_single_file_name = 'your_data.json' # 예: 'C:/Users/YourUser/Documents/single_file.json' 또는 './data/my_file.json'


# 4. 결과 파일 저장 옵션 (다중/단일 파일 처리 모두에 적용)
# True: 번역된 내용을 새로운 파일로 저장합니다. (원본 파일 보존)
# False: 원본 JSON 파일을 번역된 내용으로 덮어씁니다. (원본 파일 변경)
save_output_to_new_file_option = True 

# 새 파일에 접미사를 추가할지 여부
# True: 아래 'output_file_suffix'에 지정된 접미사를 파일명에 추가합니다.
# False: 접미사를 추가하지 않고 원본 파일명만 사용합니다.
# 경고: 'True'로 설정된 'save_output_to_new_file_option'과 'False'로 설정된 'use_custom_output_directory' 조합에서
#        'add_output_suffix'를 'False'로 설정하면 원본 파일이 덮어쓰여질 수 있습니다!
add_output_suffix = False # 이 값을 True/False로 설정하여 접미사 사용 여부 제어

# save_output_to_new_file_option이 True일 때, 새 파일에 붙일 접미사.
output_file_suffix = '_output'       # 예: 'ko', '_translated' 등 (결과 파일명: original_file_output.json)


# 5. 번역된 결과 파일의 저장 디렉터리 지정 옵션 (save_output_to_new_file_option이 True일 때만 유효)
# True: 번역된 JSON 파일을 output_json_directory에 지정된 폴더에 저장합니다.
#        이때 원본 JSON 파일의 하위 디렉터리 구조를 output_json_directory 내에 유지합니다.
# False: 원본 JSON 파일이 있던 디렉터리에 새 파일을 생성합니다.
use_custom_output_directory = True 

# use_custom_output_directory가 True일 때: 번역된 JSON 파일을 저장할 최상위 디렉터리 경로.
# 이 폴더와 그 하위의 필요한 폴더들이 스크립트가 실행될 때 자동으로 생성됩니다.
output_json_directory = './translated_output/' # 예: 'C:/Users/YourUser/Desktop/processed_json/' 또는 './output/'


# 6. 미번역 항목 보고서 생성 옵션
# True: 스크립트 완료 후 번역되지 않은 항목들을 기록한 CSV 보고서 파일을 생성합니다.
# False: 보고서를 생성하지 않습니다.
generate_untranslated_report = True 

# generate_untranslated_report가 True일 때: 보고서 파일 이름 (CSV 형식으로 저장되며, 헤더 포함).
untranslated_report_filename = 'untranslated_items_report.csv' 

# 7. JSON 파일명에 매칭되는 CSV 파일 사용 옵션 
# True: 각 JSON 파일의 기본 이름(예: data.json -> data)과 동일한 이름을 가진 CSV 파일(예: data.csv)을 먼저 찾아 사용합니다.
#        매칭되는 CSV가 없으면 위에서 설정한 'csv_file_path'를 폴백(fallback)으로 사용합니다.
# False: 모든 JSON 파일에 대해 'csv_file_path'에 지정된 단일 CSV 파일만 사용합니다.
match_csv_by_json_filename = True # JSON 파일명과 같은 CSV 파일을 사용할지 여부

# 8. 매칭 CSV 파일을 찾을 최상위 CSV 디렉터리 (match_csv_by_json_filename이 True일 때만 유효)
# 이 디렉터리 내에서 JSON 파일의 상대 경로와 일치하는 CSV 파일을 찾습니다.
# 예: json_input_directory/subdir/data.json -> csv_root_directory_for_matching/subdir/data.csv 를 찾음
csv_root_directory_for_matching = './CSV/' # 예: './Translations_CSV/' 또는 'C:/MyProject/CSVs/'

# 9. 필드 처리 설정 (어떤 JSON 파일에서 '처리하지 않을' 필드를 지정)
# 딕셔너리 형태로 JSON 파일명 (예: 'your_json_file.json')과 해당 JSON에서 '처리하지 않을' 필드 리스트를 매핑합니다.
# 'key'는 os.path.basename(json_filepath)으로 얻어지는 JSON 파일의 이름과 정확히 일치해야 합니다.
# '*' 키는 기본값으로, 명시적으로 지정되지 않은 모든 JSON 파일에 적용됩니다.
# 필드 리스트를 비워두면 (예: []) 해당 JSON 파일에서는 어떤 필드도 건너뛰지 않습니다 (모든 필드 처리).
fields_to_skip_by_json = {
    '*': [], # 모든 JSON 파일에 대한 기본값: 기본적으로 건너뛸 필드 없음 (모든 필드 처리)
    'interactions_plots.json': ["strName"], # 예시: 'interactions_plots.json' 파일은 'strName'과 'strNameFriendly' 필드를 처리하지 않음
    'interactions_pledges.json': ["strName"],
    'interactions_modeswitch.json': ["strName", "strTitle"],
    'interactions_hacking.json': ["strName"],
    'interactions_events_ffwd.json': ["strName","strTitle"],
    'interactions_encounters.json': ["strName"],
    'interactions_datafiles.json': ["strName"],
    'interactions_events_ffwd.json': ["strName"],
    'interactions.json': ["strName"],
    'condowners.json': ["strName"],
    'conditions.json': ["strName"],
    # 'another_example.json': ["strDesc", "strTooltip"], # 예시: 'another_example.json' 파일은 'strDesc'와 'strTooltip' 필드를 처리하지 않음
    # 'only_process_name_and_desc.json': ["strNameFriendly", "strNameShort", "strTitle", "strTooltip"], # 예시: 특정 필드만 제외하여 나머지 처리
}

# 10. 빈 JSON 필드 값 미번역 로그 억제 설정
# True: JSON 필드 값이 "" (빈 문자열) 또는 "None" (NoneType이 문자열로 변환된 경우) 이면서
#       CSV에 해당 원문이 없을 경우, "미번역 발견" 로그를 콘솔에 출력하지 않습니다.
#       (보고서에는 기록됩니다. 보고서에는 항상 모든 미번역 항목이 기록됨)
# False: 빈 문자열 또는 "None" 값도 다른 값과 동일하게 "미번역 발견" 로그를 출력합니다.
suppress_empty_untranslated_logs = True # 이 줄이 존재하는지, 주석 처리되지 않았는지 확인

# ====================================================================================================================================
# === 사용자 설정 끝 ===
# ====================================================================================================================================


# --- 글로벌 변수: 번역되지 않은 항목들을 저장할 리스트 ---
# 각 항목은 (JSON 파일 경로, 필드 타입 (예: 'strName'), 원문 텍스트) 형태의 튜플로 저장됩니다.
untranslated_items_report_data = []

def translate_json_file(json_filepath, csv_filepath, output_filepath, suppress_empty_untranslated_logs):
    global untranslated_items_report_data
    
    print(f"\n--- '{os.path.basename(json_filepath)}' 파일 처리 시작 ---")

    key_to_original_to_translated = {}

    # CSV 파일 로드
    try:
        # 인코딩 문제 발생 시 'utf-8' 대신 'cp949', 'euc-kr' 등을 시도
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile: 
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) >= 3:
                    compare_key = row[0].strip()
                    original_text = row[1]
                    translated_text = row[2]

                    original_text = original_text.replace('\\n', '\n')
                    translated_text = translated_text.replace('\\n', '\n')

                    if compare_key not in key_to_original_to_translated:
                        key_to_original_to_translated[compare_key] = {}
                    
                    key_to_original_to_translated[compare_key][original_text] = translated_text
        # CSV 로드 성공 메시지 (디버깅용)
        # 이 부분에 어떤 필드가 몇 개 로드되었는지 출력하는 로직 추가 가능
        print(f"CSV 파일 '{csv_filepath}' 로드 완료. ({len(key_to_original_to_translated.get('strName', {}))} strName, {len(key_to_original_to_translated.get('strDesc', {}))} strDesc, {len(key_to_original_to_translated.get('strNameFriendly', {}))} strNameFriendly, {len(key_to_original_to_translated.get('strNameShort', {}))} strNameShort, {len(key_to_original_to_translated.get('strTitle', {}))} strTitle, {len(key_to_original_to_translated.get('strTooltip', {}))} strTooltip 항목)")

    except FileNotFoundError:
        print(f"오류: CSV 파일을 찾을 수 없습니다: {csv_filepath}")
        return False
    except Exception as e:
        print(f"오류: CSV 파일 로드 중 오류 발생: {e}")
        return False

    json_data = []
    # JSON 파일 로드
    try:
        with open(json_filepath, 'r', encoding='utf-8') as jsonfile:
            json_data = json.load(jsonfile)
        print(f"JSON 파일 '{json_filepath}' 로드 완료. ({len(json_data)}개 객체)")
    except FileNotFoundError:
        print(f"오류: JSON 파일을 찾을 수 없습니다: {json_filepath}")
        return False
    except json.JSONDecodeError as e:
        print(f"오류: JSON 파일 디코딩 오류: {json_filepath} - {e}")
        return False
    except Exception as e:
        print(f"오류: JSON 파일 로드 중 오류 발생: {e}")
        return False

    changes_made = False
    new_json_data = []  

    # 현재 JSON 파일에 대해 '건너뛸' 필드 목록 결정
    json_base_name = os.path.basename(json_filepath)
    fields_to_skip_for_current_json = [] # 기본적으로 건너뛸 필드가 없다고 가정
    
    if json_base_name in fields_to_skip_by_json:
        fields_to_skip_for_current_json = fields_to_skip_by_json[json_base_name]
    elif '*' in fields_to_skip_by_json:
        fields_to_skip_for_current_json = fields_to_skip_by_json['*']
    else:
        # 안전 장치: 명시적 설정도, 기본 설정도 없는 경우, 어떤 필드도 건너뛰지 않음
        print(f"경고: fields_to_skip_by_json 설정에 '{json_base_name}' 또는 '*' 키가 없습니다. 어떤 필드도 건너뛰지 않습니다 (모든 필드 처리).")
        fields_to_skip_for_current_json = [] # 아무것도 건너뛰지 않음 (ALL_TRANSLATABLE_FIELDS가 모두 처리됨)
    
    # 실제 '처리할' 필드 목록 계산
    # ALL_TRANSLATABLE_FIELDS에서 건너뛸 필드를 제외하여 처리할 필드 목록을 만듭니다.
    effective_fields_to_process = [
        field for field in ALL_TRANSLATABLE_FIELDS if field not in fields_to_skip_for_current_json
    ]
    
    print(f"  [필드 처리 설정] '{json_base_name}' 파일은 다음 필드를 건너뜁니다: {', '.join(fields_to_skip_for_current_json) if fields_to_skip_for_current_json else '없음'}")
    print(f"  [필드 처리 설정] '{json_base_name}' 파일은 다음 필드를 처리합니다: {', '.join(effective_fields_to_process) if effective_fields_to_process else '없음'}")


    for item in json_data:
        modified_item = item.copy()

        # 'strName' 필드 처리
        if "strName" in modified_item and "strName" in effective_fields_to_process: # <-- 조건 추가
            current_strname_original = modified_item["strName"]
            if current_strname_original is not None:
                current_strname_original = str(current_strname_original)
            else:
                current_strname_original = "None" 
            strname_translations = key_to_original_to_translated.get("strName", {})
            if current_strname_original in strname_translations:
                translated_strname = strname_translations[current_strname_original]
                if modified_item["strName"] != translated_strname:
                    modified_item["strName"] = translated_strname
                    changes_made = True
            else:
                report_reason = "CSV에 해당 원문 없음"
                matched_csv_original = ""
                normalized_json_original = re.sub(r'\s+', ' ', current_strname_original).strip()
                for csv_original_key in strname_translations.keys():
                    normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                    if normalized_json_original == normalized_csv_key:
                        if current_strname_original != csv_original_key:
                            report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                            matched_csv_original = csv_original_key
                        break
                untranslated_items_report_data.append((json_filepath, "strName", current_strname_original, report_reason, matched_csv_original))
                
                # Conditionally print the log based on the new setting
                is_effectively_empty = (current_strname_original == "" or current_strname_original == "None")
                
                if not (suppress_empty_untranslated_logs and is_effectively_empty):
                    display_strname = current_strname_original[:50] + ('...' if len(current_strname_original) > 50 else '')
                    print(f"  [미번역 발견] strName: '{display_strname}' ({report_reason})")

        # 'strDesc' 필드 처리
        if "strDesc" in modified_item and "strDesc" in effective_fields_to_process: # <-- 조건 추가
            current_strdesc_original = modified_item["strDesc"]
            if current_strdesc_original is not None:
                current_strdesc_original = str(current_strdesc_original)
            else:
                current_strdesc_original = "None" 
            strdesc_translations = key_to_original_to_translated.get("strDesc", {})

            if current_strdesc_original in strdesc_translations:
                translated_strdesc = strdesc_translations[current_strdesc_original]
                if modified_item["strDesc"] != translated_strdesc:
                    modified_item["strDesc"] = translated_strdesc
                    changes_made = True
            else: # current_strdesc_original이 CSV 번역 맵에 직접 존재하지 않는 경우
                report_reason = "CSV에 해당 원문 없음"
                matched_csv_original = ""
                normalized_json_original = re.sub(r'\s+', ' ', current_strdesc_original).strip() 
                for csv_original_key in strdesc_translations.keys():
                    normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                    if normalized_json_original == normalized_csv_key:
                        if current_strdesc_original != csv_original_key:
                            report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                            matched_csv_original = csv_original_key
                        break 
                untranslated_items_report_data.append((json_filepath, "strDesc", current_strdesc_original, report_reason, matched_csv_original))
                
                # Conditionally print the log based on the new setting
                is_effectively_empty = (current_strdesc_original == "" or current_strdesc_original == "None")
                
                if not (suppress_empty_untranslated_logs and is_effectively_empty):
                    display_strdesc = current_strdesc_original[:50] + ('...' if len(current_strdesc_original) > 50 else '')
                    print(f"  [미번역 발견] strDesc: '{display_strdesc}' ({report_reason})")

        # 'strNameFriendly' 필드 처리
        if "strNameFriendly" in modified_item and "strNameFriendly" in effective_fields_to_process: # <-- 조건 추가
            current_strnamefriendly_original = modified_item["strNameFriendly"]
            if current_strnamefriendly_original is not None:
                current_strnamefriendly_original = str(current_strnamefriendly_original)
            else:
                current_strnamefriendly_original = "None" 
            strnamefriendly_translations = key_to_original_to_translated.get("strNameFriendly", {})
            if current_strnamefriendly_original in strnamefriendly_translations:
                translated_strnamefriendly = strnamefriendly_translations[current_strnamefriendly_original]
                if modified_item["strNameFriendly"] != translated_strnamefriendly:
                    modified_item["strNameFriendly"] = translated_strnamefriendly
                    changes_made = True
            else:
                report_reason = "CSV에 해당 원문 없음"
                matched_csv_original = ""
                normalized_json_original = re.sub(r'\s+', ' ', current_strnamefriendly_original).strip()
                for csv_original_key in strnamefriendly_translations.keys():
                    normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                    if normalized_json_original == normalized_csv_key:
                        if current_strnamefriendly_original != csv_original_key:
                            report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                            matched_csv_original = csv_original_key
                        break
                untranslated_items_report_data.append((json_filepath, "strNameFriendly", current_strnamefriendly_original, report_reason, matched_csv_original))
                
                # Conditionally print the log based on the new setting
                is_effectively_empty = (current_strnamefriendly_original == "" or current_strnamefriendly_original == "None")
                
                if not (suppress_empty_untranslated_logs and is_effectively_empty):
                    display_strnamefriendly = current_strnamefriendly_original[:50] + ('...' if len(current_strnamefriendly_original) > 50 else '')
                    print(f"  [미번역 발견] strNameFriendly: '{display_strnamefriendly}' ({report_reason})")

        # 'strNameShort' 필드 처리
        if "strNameShort" in modified_item and "strNameShort" in effective_fields_to_process: # <-- 조건 추가
            current_strnameshort_original = modified_item["strNameShort"]
            if current_strnameshort_original is not None:
                current_strnameshort_original = str(current_strnameshort_original)
            else:
                current_strnameshort_original = "None" 
            strnameshort_translations = key_to_original_to_translated.get("strNameShort", {})
            if current_strnameshort_original in strnameshort_translations:
                translated_strnameshort = strnameshort_translations[current_strnameshort_original]
                if modified_item["strNameShort"] != translated_strnameshort:
                    modified_item["strNameShort"] = translated_strnameshort
                    changes_made = True
            else:
                report_reason = "CSV에 해당 원문 없음"
                matched_csv_original = ""
                normalized_json_original = re.sub(r'\s+', ' ', current_strnameshort_original).strip()
                for csv_original_key in strnameshort_translations.keys():
                    normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                    if normalized_json_original == normalized_csv_key:
                        if current_strnameshort_original != csv_original_key:
                            report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                            matched_csv_original = csv_original_key
                        break
                
                # Conditionally print the log based on the new setting
                is_effectively_empty = (current_strnameshort_original == "" or current_strnameshort_original == "None")
                
                if not (suppress_empty_untranslated_logs and is_effectively_empty):
                    display_strnameshort = current_strnameshort_original[:50] + ('...' if len(current_strnameshort_original) > 50 else '')
                    print(f"  [미번역 발견] strNameShort: '{display_strnameshort}' ({report_reason})")

        # 'strTitle' 필드 처리 (수정된 변수명 및 보고서 타입)
        if "strTitle" in modified_item and "strTitle" in effective_fields_to_process: # <-- 조건 추가
            current_strtitle_original = modified_item["strTitle"]
            if current_strtitle_original is not None:
                current_strtitle_original = str(current_strtitle_original)
            else:
                current_strtitle_original = "None" 
            strtitle_translations = key_to_original_to_translated.get("strTitle", {})
            if current_strtitle_original in strtitle_translations:
                translated_strtitle = strtitle_translations[current_strtitle_original]
                if modified_item["strTitle"] != translated_strtitle:
                    modified_item["strTitle"] = translated_strtitle
                    changes_made = True
            else:
                report_reason = "CSV에 해당 원문 없음"
                matched_csv_original = ""
                normalized_json_original = re.sub(r'\s+', ' ', current_strtitle_original).strip()
                for csv_original_key in strtitle_translations.keys():
                    normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                    if normalized_json_original == normalized_csv_key:
                        if current_strtitle_original != csv_original_key:
                            report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                            matched_csv_original = csv_original_key
                        break
                
                # Conditionally print the log based on the new setting
                is_effectively_empty = (current_strtitle_original == "" or current_strtitle_original == "None")
                
                if not (suppress_empty_untranslated_logs and is_effectively_empty):
                    display_strtitle = current_strtitle_original[:50] + ('...' if len(current_strtitle_original) > 50 else '')
                    print(f"  [미번역 발견] strTitle: '{display_strtitle}' ({report_reason})")

        # 'strTooltip' 필드 처리 (이전 대소문자 문제 해결 및 조건 추가)
        if "strTooltip" in modified_item and "strTooltip" in effective_fields_to_process: # <-- 조건 추가
            current_strtooltip_original = modified_item["strTooltip"]
            if current_strtooltip_original is not None:
                current_strtooltip_original = str(current_strtooltip_original)
            else:
                current_strtooltip_original = "None"
            strtooltip_translations = key_to_original_to_translated.get("strTooltip", {}) # <-- "strTooltip"으로 변경
            if current_strtooltip_original in strtooltip_translations:
                translated_strtooltip = strtooltip_translations[current_strtooltip_original]
                if modified_item["strTooltip"] != translated_strtooltip:
                    modified_item["strTooltip"] = translated_strtooltip
                    changes_made = True
            else:
                report_reason = "CSV에 해당 원문 없음"
                matched_csv_original = ""
                normalized_json_original = re.sub(r'\s+', ' ', current_strtooltip_original).strip()
                for csv_original_key in strtooltip_translations.keys():
                    normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                    if normalized_json_original == normalized_csv_key:
                        if current_strtooltip_original != csv_original_key:
                            report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                            matched_csv_original = csv_original_key
                        break
                
                # Conditionally print the log based on the new setting
                is_effectively_empty = (current_strtooltip_original == "" or current_strtooltip_original == "None")
                
                if not (suppress_empty_untranslated_logs and is_effectively_empty):
                    display_strtooltip = current_strtooltip_original[:50] + ('...' if len(current_strtooltip_original) > 50 else '')
                    print(f"  [미번역 발견] strTooltip: '{display_strtooltip}' ({report_reason})")


        new_json_data.append(modified_item)

    if changes_made:
        try:
            output_dir = os.path.dirname(output_filepath)
            if output_dir and not os.path.exists(output_dir): 
                os.makedirs(output_dir, exist_ok=True)
                print(f"하위 출력 디렉터리 '{output_dir}'를 생성했습니다.")

            with open(output_filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(new_json_data, jsonfile, indent=4, ensure_ascii=False)
            print(f"JSON 파일 '{output_filepath}'에 변경사항이 성공적으로 저장되었습니다.")
        except Exception as e:
            print(f"JSON 파일 쓰기 중 오류 발생: {e}")
    else:
        print("JSON 파일에 변경할 내용이 없습니다.")
    
    print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")


# ====================================================================================================================================
# === 다중 파일 처리 기능 ===
# ====================================================================================================================================

def process_multiple_json_files(json_input_directory, default_csv_filepath, save_output_to_new_file=True, output_suffix='_output', use_custom_output_directory=False, output_json_directory=None, match_csv_by_json=False, csv_root_for_matching=None, add_output_suffix=True, suppress_empty_untranslated_logs=False): # 마지막에 추가
    """
    지정된 디렉터리 내의 모든 JSON 파일을 찾아 번역 처리합니다.

    Args:
        json_input_directory (str): JSON 파일들이 위치한 디렉터리 경로.
        default_csv_filepath (str): 매칭되는 CSV가 없을 때 사용할 기본 CSV 파일의 경로.
        save_output_to_new_file (bool): True이면 '_output' 접미사를 붙여 새 파일로 저장. False이면 원본 덮어쓰기.
        output_suffix (str): 새 파일에 붙일 접미사.
        use_custom_output_directory (bool): True이면 output_json_directory에 계층 구조를 유지하며 저장.
        output_json_directory (str): 번역된 JSON 파일을 저장할 루트 디렉터리 경로.
        match_csv_by_json (bool): JSON 파일명에 매칭되는 CSV 파일을 사용할지 여부.
        csv_root_for_matching (str): 매칭 CSV 파일을 찾을 최상위 CSV 디렉터리 (match_csv_by_json이 True일 때 사용).
        add_output_suffix (bool): 출력 파일명에 접미사를 추가할지 여부.
    """
    print(f"\n===== '{json_input_directory}' 디렉터리 내 JSON 파일 처리 시작 =====")

    if not os.path.isdir(json_input_directory):
        print(f"오류: 지정된 JSON 입력 디렉터리를 찾을 수 없습니다: '{json_input_directory}'")
        print("===== JSON 파일 처리 종료 =====")
        return

    # csv_root_for_matching 경로 유효성 검사 (매칭 모드이고, 해당 경로가 지정된 경우)
    if match_csv_by_json and csv_root_for_matching:
        if not os.path.isdir(csv_root_for_matching):
            print(f"경고: CSV 매칭을 위한 최상위 디렉터리 '{csv_root_for_matching}'을(를) 찾을 수 없습니다. "
                  "매칭 CSV 검색 시 이 경로를 건너뛰고 JSON 파일과 동일한 디렉터리만 확인합니다.")
            csv_root_for_matching = None # 찾지 못했음을 표시

    json_files_found = []
    try:
        # os.walk를 사용하여 하위 디렉토리까지 재귀적으로 JSON 파일 탐색
        for root, _, files in os.walk(json_input_directory):
            for file in files:
                if file.lower().endswith('.json'):
                    json_files_found.append(os.path.join(root, file))

    except Exception as e:
        print(f"오류: '{json_input_directory}' 디렉터리 탐색 중 오류 발생: {e}")
        print("===== JSON 파일 처리 종료 =====")
        return
    
    if not json_files_found:
        print(f"정보: '{json_input_directory}' 디렉터리에서 처리할 JSON 파일을 찾을 수 없습니다.")
        print("===== JSON 파일 처리 종료 =====")
        return
    
    print(f"'{json_input_directory}'에서 {len(json_files_found)}개의 JSON 파일을 찾았습니다.")

    for i, json_filepath in enumerate(json_files_found):
        print(f"\n--- [{i+1}/{len(json_files_found)}] 파일: {os.path.basename(json_filepath)} 처리 중 ---")

        # 사용할 CSV 파일 경로 결정
        current_csv_to_use = default_csv_filepath # 기본적으로는 기본 CSV를 사용
        if match_csv_by_json:
            json_base_name = os.path.splitext(os.path.basename(json_filepath))[0]
            
            found_matching_csv = False

            # 1. csv_root_for_matching에서 매칭 CSV 시도
            if csv_root_for_matching:
                relative_path_from_json_root = os.path.relpath(json_filepath, json_input_directory)
                # 예: 'subdir/data.json' -> 'subdir/data.csv'
                potential_csv_path_in_root = os.path.join(csv_root_for_matching, relative_path_from_json_root.replace('.json', '.csv'))
                
                if os.path.exists(potential_csv_path_in_root):
                    current_csv_to_use = potential_csv_path_in_root
                    print(f"  [CSV 매칭] '{os.path.basename(json_filepath)}'에 대해 '{os.path.basename(potential_csv_path_in_root)}' (지정된 CSV 루트에서) 사용.")
                    found_matching_csv = True

            # 2. JSON 파일과 동일한 디렉터리에서 매칭 CSV 시도 (1번에서 찾지 못했을 경우)
            if not found_matching_csv:
                matching_csv_path_in_json_dir = os.path.join(os.path.dirname(json_filepath), f"{json_base_name}.csv")
                
                if os.path.exists(matching_csv_path_in_json_dir):
                    current_csv_to_use = matching_csv_path_in_json_dir
                    print(f"  [CSV 매칭] '{os.path.basename(json_filepath)}'에 대해 '{os.path.basename(matching_csv_path_in_json_dir)}' (JSON 파일과 동일 디렉터리에서) 사용.")
                    found_matching_csv = True
            
            # 3. 모든 매칭 시도 실패 시 기본 CSV 사용
            if not found_matching_csv:
                print(f"  [경고] '{os.path.basename(json_filepath)}'에 대한 매칭 CSV를 찾을 수 없습니다. 기본 CSV '{os.path.basename(default_csv_filepath)}'를 사용합니다.")
                current_csv_to_use = default_csv_filepath # Fallback to default


        if save_output_to_new_file:
            base_name, ext = os.path.splitext(os.path.basename(json_filepath)) # 파일명만 추출하여 확장자 분리
            
            # 여기서 접미사 사용 여부를 결정합니다.
            actual_suffix_to_use = output_suffix if add_output_suffix else ''
            current_output_filename = f"{base_name}{actual_suffix_to_use}{ext}"
            
            if use_custom_output_directory:
                # 원본 디렉터리 내에서의 상대 경로 추출 (예: 'subdir/data.json')
                relative_path_to_input_dir = os.path.relpath(json_filepath, json_input_directory)
                # 상대 경로에서 디렉터리 부분만 추출 (예: 'subdir')
                relative_output_subdir = os.path.dirname(relative_path_to_input_dir)
                
                # 최종 출력 디렉터리 경로 생성 (예: 'translated_output/subdir/')
                target_output_dir = os.path.join(output_json_directory, relative_output_subdir)
                
                # 최종 출력 파일 경로 생성 (예: 'translated_output/subdir/data_output.json')
                current_output_filepath = os.path.join(target_output_dir, current_output_filename)
                
            else:
                # 커스텀 디렉터리 사용 안함 -> 원본 파일과 같은 디렉터리에 저장
                current_output_filepath = os.path.join(os.path.dirname(json_filepath), current_output_filename)
        else:
            current_output_filepath = json_filepath # 원본 파일 덮어쓰기
        
        translate_json_file(json_filepath, current_csv_to_use, current_output_filepath, suppress_empty_untranslated_logs) # suppress_empty_untranslated_logs 인자 전달
    
    print(f"\n===== '{json_input_directory}' 디렉터리 내 JSON 파일 처리 완료 =====")


# ====================================================================================================================================
# === 스크립트 실행 로직 ===
# (사용자 설정에 따라 위에서 정의된 함수들을 호출합니다.)
# ====================================================================================================================================
print("\n--- 스크립트 실행 시작 ---")

# 커스텀 출력 루트 디렉터리 사용 시 최상위 폴더 생성
# (하위 폴더는 각 파일 처리 시 translate_json_file 내부에서 자동으로 생성됨)
if use_custom_output_directory and save_output_to_new_file_option:
    if not os.path.exists(output_json_directory):
        try:
            os.makedirs(output_json_directory, exist_ok=True)
            print(f"최상위 출력 디렉터리 '{output_json_directory}'를 생성했습니다.")
        except Exception as e:
            print(f"오류: 최상위 출력 디렉터리 '{output_json_directory}' 생성 실패: {e}")
            exit() # 디렉터리 생성 실패 시 스크립트 중단

if process_all_files_in_directory:
    # process_multiple_json_files 함수에 새로운 출력 디렉터리 관련 인자 전달
    process_multiple_json_files(json_input_directory, csv_file_path, # csv_file_path를 default_csv_filepath로 전달
                                 save_output_to_new_file_option, output_file_suffix,
                                 use_custom_output_directory, output_json_directory,
                                 match_csv_by_json_filename, csv_root_directory_for_matching, add_output_suffix,
                                 suppress_empty_untranslated_logs) # suppress_empty_untranslated_logs 인자 전달
else:
    # 단일 파일 처리 함수 호출
    # 사용할 CSV 파일 경로 결정
    current_csv_to_use = csv_file_path # 기본적으로는 기본 CSV를 사용
    if match_csv_by_json_filename:
        json_base_name = os.path.splitext(os.path.basename(json_single_file_name))[0]
        found_matching_csv = False

        # 1. csv_root_directory_for_matching에서 매칭 CSV 시도
        if csv_root_directory_for_matching and os.path.isdir(csv_root_directory_for_matching):
            # 단일 파일이므로 json_input_directory를 사용하지 않고, os.path.dirname으로 직접 상대 경로를 계산
            # 예: json_single_file_name = 'input_subdir/data.json'
            # relative_dir = 'input_subdir'
            relative_dir = os.path.dirname(json_single_file_name)
            if not relative_dir: # 파일명만 있는 경우 현재 디렉토리로 간주
                relative_dir = '.' 

            potential_csv_path_in_root = os.path.join(csv_root_directory_for_matching, relative_dir, f"{json_base_name}.csv")
            
            if os.path.exists(potential_csv_path_in_root):
                current_csv_to_use = potential_csv_path_in_root
                print(f"  [CSV 매칭] '{os.path.basename(json_single_file_name)}'에 대해 '{os.path.basename(potential_csv_path_in_root)}' (지정된 CSV 루트에서) 사용.")
                found_matching_csv = True

        # 2. JSON 파일과 동일한 디렉터리에서 매칭 CSV 시도 (1번에서 찾지 못했을 경우)
        if not found_matching_csv:
            matching_csv_path_in_json_dir = os.path.join(os.path.dirname(json_single_file_name), f"{json_base_name}.csv")

            if os.path.exists(matching_csv_path_in_json_dir):
                current_csv_to_use = matching_csv_path_in_json_dir
                print(f"  [CSV 매칭] '{os.path.basename(json_single_file_name)}'에 대해 '{os.path.basename(matching_csv_path_in_json_dir)}' (JSON 파일과 동일 디렉터리에서) 사용.")
                found_matching_csv = True
        
        # 3. 모든 매칭 시도 실패 시 기본 CSV 사용
        if not found_matching_csv:
            print(f"  [경고] '{os.path.basename(json_single_file_name)}'에 대한 매칭 CSV를 찾을 수 없습니다. 기본 CSV '{os.path.basename(csv_file_path)}'를 사용합니다.")
            current_csv_to_use = csv_file_path # Fallback to default


    if save_output_to_new_file_option:
        base_name, ext = os.path.splitext(os.path.basename(json_single_file_name))
        
        # 여기서 접미사 사용 여부를 결정합니다.
        actual_suffix_to_use = output_file_suffix if add_output_suffix else ''
        current_output_filename = f"{base_name}{actual_suffix_to_use}{ext}"
        
        if use_custom_output_directory:
            relative_input_subdir = os.path.dirname(json_single_file_name)
            output_target_filepath = os.path.join(output_json_directory, relative_input_subdir, current_output_filename)
        else:
            input_file_dir = os.path.dirname(json_single_file_name)
            if not input_file_dir: 
                input_file_dir = '.'
            output_target_filepath = os.path.join(input_file_dir, current_output_filename)
    else:
        output_target_filepath = json_single_file_name
    
    translate_json_file(json_single_file_name, current_csv_to_use, output_target_filepath, suppress_empty_untranslated_logs) # suppress_empty_untranslated_logs 인자 전달

# --- 미번역 항목 보고서 생성 (모든 JSON 파일 처리 완료 후) ---
if generate_untranslated_report:
    if untranslated_items_report_data: # 수집된 미번역 항목이 있을 경우
        print(f"\n--- 미번역 항목 보고서 생성 중: '{untranslated_report_filename}' ---")
        try:
            with open(untranslated_report_filename, 'w', newline='', encoding='utf-8') as report_file:
                report_writer = csv.writer(report_file)
                # CSV 헤더 작성: 변경된 데이터 구조에 맞춰 헤더 추가
                report_writer.writerow(['JSON File Path', 'Field Type', 'Original Text (from JSON)', 'Reason for Not Translating', 'Matching CSV Original Text'])
                # 수집된 데이터 쓰기
                for item_info in untranslated_items_report_data:
                    report_writer.writerow(item_info)
            print("미번역 항목 보고서가 성공적으로 생성되었습니다.")
        except Exception as e:
            print(f"오류: 미번역 항목 보고서 생성 중 오류 발생: {e}")
    else: # 수집된 미번역 항목이 없을 경우
        print("정보: 모든 항목이 번역되었거나, 미번역 항목이 없으므로 보고서 파일이 생성되지 않습니다.")

print("\n--- 스크립트 실행 완료 ---")