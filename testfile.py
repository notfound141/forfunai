import os
import json
import csv
import re # 정규표현식 모듈 추가 (필요한 경우)
from collections import defaultdict

# 전역 변수 (이 부분은 환경설정 파일에 정의되거나 함수의 인자로 전달되어야 합니다.)
# untranslated_items_report_data = []
# duplicate_original_texts = defaultdict(list)
# duplicate_translated_texts = defaultdict(list)
# OUTPUT_DUPLICATION_SETTINGS = {'detect_duplicate_original_text': True, 'detect_duplicate_translated_text': True}
# suppress_empty_untranslated_logs = False # 이 값은 전역이거나 인자로 받아야 함

# _check_and_report_duplicates 함수는 기존처럼 유지되어야 합니다.
# def _check_and_report_duplicates(text_type, text_value, file_path, duplicate_collection, report_data_list, original_text_for_translated=None):
#     # ... 기존 _check_and_report_duplicates 함수 내용 ...

# ====================================================================================================================================
# === 0. 설정: 사용자 옵션 및 파일 경로 지정 ===
# ====================================================================================================================================

# ------------------------------------------------------------------------------------------------------------------------------------
# 0.1. JSON 파일 처리 옵션
# ------------------------------------------------------------------------------------------------------------------------------------
# 단일 JSON 파일만 처리할지, 아니면 지정된 디렉터리 내의 모든 JSON 파일을 처리할지 선택합니다.
process_all_files_in_directory = True # True: 디렉터리 내 모든 JSON 처리, False: 단일 JSON 파일만 처리

# 단일 파일 처리 시
json_single_file_name = "example_single_file.json" # process_all_files_in_directory가 False일 때만 사용

# 디렉터리 내 모든 파일 처리 시
# 영문 원본 json 파일들의 상위 디렉토리
json_input_directory = "./EN_json/" # process_all_files_in_directory가 True일 때만 사용
# 예: "C:/Users/UserName/Documents/MyProject/json_files"

# ------------------------------------------------------------------------------------------------------------------------------------
# 0.2. CSV 파일 처리 옵션 (번역 데이터)
# ------------------------------------------------------------------------------------------------------------------------------------
# 모든 JSON 파일에 적용될 기본 CSV 파일 경로입니다.
csv_file_path = "./CSV/default_translation.csv" # 기본 CSV 파일 경로
# 예: "C:/Users/UserName/Documents/MyProject/translations/base_translations.csv"

# JSON 파일명과 동일한 CSV 파일을 찾아 사용할지 여부 (예: item.json -> item.csv)
match_csv_by_json_filename = True # True: JSON과 동일한 이름의 CSV 우선 사용, False: 무조건 default_csv_filepath 사용

# match_csv_by_json_filename이 True일 때, 매칭 CSV 파일을 찾을 최상위 루트 디렉터리 (선택 사항)
# 설정하지 않으면 (None), JSON 파일과 동일한 디렉터리에서만 찾습니다.
# 여기에 경로를 지정하면, JSON 파일의 상대 경로를 기준으로 해당 루트 디렉터리에서 매칭 CSV를 찾습니다.
csv_root_directory_for_matching = "./CSV/" # 예: "C:/Users/UserName/Documents/MyProject/csv_data"

# ------------------------------------------------------------------------------------------------------------------------------------
# 0.3. 출력 파일 및 디렉터리 옵션
# ------------------------------------------------------------------------------------------------------------------------------------
# 번역된 JSON 파일을 새 파일로 저장할지 여부. False이면 원본 파일을 덮어씁니다.
save_output_to_new_file_option = True # True: 새 파일로 저장, False: 원본 덮어쓰기

# 새 파일 저장 시 파일명에 추가할 접미사 (예: original.json -> original_output.json)
output_file_suffix = "" # save_output_to_new_file_option이 True일 때만 사용

# 출력 파일을 사용자 지정 디렉터리에 저장할지 여부 (원본 디렉터리 구조 유지)
use_custom_output_directory = True # True: output_json_directory에 저장, False: 원본 JSON과 같은 디렉터리에 저장

# 사용자 지정 출력 디렉터리 경로 (use_custom_output_directory가 True일 때만 사용)
output_json_directory = "translated_output"
# 예: "C:/Users/UserName/Documents/MyProject/translated_output"

# 출력 파일명에 접미사를 추가할지 여부 (output_file_suffix와 별개로 동작)
# False로 설정하면, save_output_to_new_file_option이 True여도 접미사 없이 파일명만 유지됩니다.
# (예: item.json -> translated_json_output/item.json)
add_output_suffix = True # True: 접미사 추가, False: 접미사 사용 안 함

# ------------------------------------------------------------------------------------------------------------------------------------
# 0.4. 보고서 및 로깅 옵션
# ------------------------------------------------------------------------------------------------------------------------------------
# 번역되지 않은 항목에 대한 보고서 CSV 파일을 생성할지 여부
generate_untranslated_report = True

# 미번역 항목 보고서 파일명
untranslated_report_filename = "untranslated_report.csv"

# 비어있거나 "None"인 원본 텍스트가 번역되지 않았을 경우 로그 및 보고서에 추가하지 않을지 여부
# (예: JSON에 "strName": "" 또는 "strName": None 인 경우)
suppress_empty_untranslated_logs = True

# ------------------------------------------------------------------------------------------------------------------------------------
# 0.5. aValues 필드 병합 설정 (새로운 기능)
# ------------------------------------------------------------------------------------------------------------------------------------
# 'aValues' 필드 병합 모드
# 'off': aValues 병합 기능 사용 안 함
# 'all_files': 모든 JSON 파일에 대해 'json_avalues_reference_root_directory'의 동일 상대 경로 JSON 참조
# 'specific_files': 'specific_merge_configs'에 정의된 파일만 참조
json_avalues_merge_settings = {
    'merge_mode': 'specific_files', # 'off', 'all_files', 'specific_files' 중 하나
    'reference_json_root_directory': 'CSV', # 'all_files' 모드에서 참조 JSON 파일들의 루트 디렉터리
    'specific_merge_configs': [ # 'specific_files' 모드에서 사용할 특정 파일별 설정
        {
            'source_json_basename': 'ItemData.json', # 병합을 적용할 원본 JSON 파일의 기본 이름
            'reference_json_root_directory': 'aValues_reference_data', # 해당 JSON 파일이 참조할 JSON 루트 디렉터리
            'match_key_index': 0, # aValues 배열 청크 내에서 매칭 키로 사용할 값의 인덱스 (0부터 시작)
            'copy_value_indices': [1, 2,] # 참조 JSON에서 현재 JSON으로 복사할 값들의 인덱스 목록
        },
        {
            'source_json_basename': 'conditions_simple.json',
            'reference_json_root_directory': 'CSV',
            'match_key_index': 0,
            'copy_value_indices': [1, 2]
        }
        # 필요한 만큼 더 추가할 수 있습니다.
    ]
}

# aValues 배열의 각 데이터 묶음(청크)의 크기 (예: [key, val1, val2, ..., valN]의 총 개수)
# 이 값은 'aValues' 배열이 어떤 일정한 패턴으로 반복되는 경우에 사용됩니다.
avalues_chunk_size = 7 # 현재 코드가 7개 항목을 한 묶음으로 가정하고 있음.


# ------------------------------------------------------------------------------------------------------------------------------------
# 0.6. OUTPUT_DUPLICATION_SETTINGS (사용자 요청에 따라 모든 기능 False로 설정)
# ------------------------------------------------------------------------------------------------------------------------------------
# 중복 감지 및 처리 설정
OUTPUT_DUPLICATION_SETTINGS = {
    'detect_duplicate_original_text': False, # 원본 텍스트 중복 감지 및 보고서에 추가 여부
    'detect_duplicate_translated_text': False, # 번역 텍스트 중복 감지 및 보고서에 추가 여부
    'report_duplicates_only_once': False # 동일한 중복 쌍을 보고서에 한 번만 추가할지 여부
}

# ------------------------------------------------------------------------------------------------------------------------------------
# 0.7. 번역 대상 문자열 필드 설정 (새로 추가)
# ------------------------------------------------------------------------------------------------------------------------------------
# JSON 객체 내에서 번역을 수행할 문자열 필드 목록입니다.
# 여기에 필드 이름을 추가하면 해당 필드가 번역 대상에 포함됩니다.
translation_target_fields = [
    "strName",
    "strNameFriendly",
    "strDesc",
    "strNameShort",
    "strTitle",
    "strTooltip",
    "strBody" # 예시: 새로 추가할 필드
]

# ====================================================================================================================================
# === JSON-to-JSON 직접 병합 설정 ===
# ====================================================================================================================================
# 특정 JSON 파일의 내용을 다른 JSON 파일의 내용으로 직접 덮어쓰는 기능.
# 예를 들어, 영어 JSON의 'aValues'를 한국어 JSON의 'aValues'로 대체할 때 사용.
json_direct_merge_settings = {
    'enable_direct_merge': True, # 이 기능을 활성화할지 여부
    'merge_rules': [ # 단일 파일 대신, 규칙 기반으로 여러 파일을 처리하도록 변경
        {
            "target_root_directory": "./EN_json/", # 병합 대상 JSON 파일들을 재귀적으로 탐색할 루트 디렉터리
            "reference_root_directory": "./KR_json/", # 참조 JSON 파일들을 재귀적으로 탐색할 루트 디렉터리
            "file_patterns": ["conditions_simple.json"], # 이 규칙을 적용할 파일 패턴 (예: ["conditions_simple.json", "data_*.json"])
                                                        # 빈 리스트일 경우 target_root_directory 내 모든 JSON 파일에 적용
            "fields_to_merge": ["aValues"], # 참조 JSON에서 타겟 JSON으로 복사할 필드 목록.
                                            # aValues 필드 자체가 병합 대상이 아니라, 그 내부 인덱스가 대상이므로 이 필드는
                                            # "aValues"가 특별 처리됨을 나타내는 마커로 사용될 수 있습니다.
                                            # 혹은 이 리스트에 "aValues"가 없으면 일반 필드처럼 처리, 있으면 특별 처리로 구분.

            # === 'aValues' 특정 병합 조건 추가 ===
            # fields_to_merge에 'aValues'가 포함되어 있고, 이 설정들이 명시될 경우 사용됩니다.
            "avalues_merge_config": {
                "match_key_index": 0,       # aValues 배열 내에서 매칭 키로 사용할 인덱스 (예: 인덱스 0)
                "copy_value_indices": [1, 2] # 매칭 성공 시 복사할 aValues 배열 내 인덱스 목록 (예: 인덱스 1, 2)
            },
            # ==================================

            "id_field": "None", # 일반적인 단일 문자열 필드 ID는 사용하지 않음을 명시. (혹은 빈 문자열 "" 사용)
                                # (aValues 내 인덱스 0을 ID처럼 사용하므로)
            "output_suffix": "_korean", # 병합된 파일에 추가할 접미사 (예: conditions_simple_korean.json)
        },
        # 다른 일반 JSON 필드 병합 규칙이 있다면 여기에 추가
        # {
        #     "target_root_directory": "./EN_json/",
        #     "reference_root_directory": "./KR_json/",
        #     "file_patterns": ["item_*.json"], # 예: item_1.json, item_2.json 등
        #     "fields_to_merge": ["strName", "strDescription"], # strName, strDescription 필드를 일반적인 방식으로 병합
        #     "id_field": "ID", # "ID" 필드를 기준으로 매칭
        #     "output_suffix": "_merged"
        # },
    ]
}

# ====================================================================================================================================
# === 2. JSON-JSON 치환 번역 설정 (새로운 기능 제안) ===
# ====================================================================================================================================
json_substitution_settings = {
    'enable_substitution': True, # JSON-JSON 치환 번역 기능 활성화 여부
    'substitution_rules': [
        {
            'name': '특정 ID를 가진 JSON의 필드 치환',
            'enabled': True,
            'target_root_directory': 'JSON_Input', # 치환 대상 JSON 파일이 있는 루트 디렉터리 (재귀 탐색)
            'reference_root_directory': 'Reference_JSONs', # 참조 JSON 파일이 있는 루트 디렉터리 (재귀 탐색)
            'file_patterns': [], # 특정 파일만 대상으로 하려면 ['file1.json', 'file2.json'], 비어있으면 모든 JSON 파일
            'match_field': 'id', # 대상 JSON과 참조 JSON을 매칭시킬 ID 필드 (예: "id" 또는 "strID")
            'substitution_fields': [ # 치환할 필드 목록
                {'target_field': 'strName', 'reference_field': 'translatedName'}, # 대상의 strName을 참조의 translatedName으로 치환
                {'target_field': 'description', 'reference_field': 'koreanDescription'},
                # {'target_field': 'aValues', 'reference_field': 'aValues', 'avalues_config': {'match_key_index': 0, 'copy_value_indices': [1, 2]}},
                # aValues 특수 처리는 별도 함수 또는 더 복잡한 로직으로 분리하는 것을 고려
            ],
            'output_suffix': '_substituted', # 치환된 파일에 붙일 접미사
            # 'use_relative_path_for_ref': True, # 대상 JSON의 상대 경로를 기준으로 참조 JSON 탐색 여부 (복잡도 증가)
        },
        # 추가 규칙 정의 가능
    ],
    # 'substitution_output_directory': 'Substituted_Output', # 치환된 JSON을 저장할 별도 루트 디렉터리 (use_custom_output_directory가 True일 때)
    # 'overwrite_original': False, # True면 원본 파일을 덮어쓰기 (save_output_to_new_file과 유사)
}

# ====================================================================================================================================
# === 1. 전역 변수 및 헬퍼 함수 ===
# ====================================================================================================================================

# 미번역 항목 데이터를 수집할 전역 리스트
untranslated_items_report_data = []

# aValues 참조 데이터를 캐싱할 딕셔너리
json_avalues_reference_data = {}

# 번역 대상 필드들을 추적할 전역 변수 (이 변수가 _process_string_field에서 사용됩니다)
effective_fields_to_process = [] # 이 라인을 추가

# 중복 감지를 위한 딕셔너리 (전역으로 관리)
duplicate_original_texts = {} # 이 라인을 추가
duplicate_translated_texts = {} # 이 라인을 추가

# CSV 맵을 캐싱하기 위한 전역 딕셔너리 (load_csv_to_translation_map에서 사용)
loaded_translation_maps = {} # 여기에 선언 위치를 옮겼습니다.


def _apply_substitution_to_item(modified_item, reference_item, substitution_fields, target_json_filepath, untranslated_items_report_data):
    """
    단일 JSON 아이템에 대해 정의된 치환 필드를 적용합니다.
    """
    changes_made_in_item = False
    
    for sub_field_config in substitution_fields:
        target_field = sub_field_config['target_field']
        reference_field = sub_field_config['reference_field']
        avalues_config = sub_field_config.get('avalues_config') # aValues 특수 처리 설정
        
        if avalues_config and target_field == "aValues" and isinstance(modified_item.get("aValues"), list):
            # === 'aValues' 특별 치환 처리 (기존 translate_json_file 로직에서 가져옴) ===
            avalues_match_idx = avalues_config["match_key_index"]
            avalues_copy_indices = avalues_config["copy_value_indices"]
            avalues_chunk_size_in_target = avalues_config.get("chunk_size", 3) # 설정에서 chunk_size 가져오기, 기본값 3
            
            avalues_changes_in_chunk = 0
            
            for i in range(0, len(modified_item["aValues"]), avalues_chunk_size_in_target):
                current_target_chunk = modified_item["aValues"][i : i + avalues_chunk_size_in_target]

                if len(current_target_chunk) > avalues_match_idx:
                    target_match_value = str(current_target_chunk[avalues_match_idx])

                    # 참조 데이터에서 매칭되는 'aValues' 청크 찾기
                    found_ref_chunk = None
                    if "aValues" in reference_item and isinstance(reference_item["aValues"], list):
                        for j in range(0, len(reference_item["aValues"]), avalues_chunk_size_in_target):
                            current_ref_chunk = reference_item["aValues"][j : j + avalues_chunk_size_in_target]
                            if len(current_ref_chunk) > avalues_match_idx and \
                               str(current_ref_chunk[avalues_match_idx]) == target_match_value:
                                found_ref_chunk = current_ref_chunk
                                break
                    
                    if found_ref_chunk:
                        # 매칭되는 청크를 찾았으면 지정된 인덱스의 값을 복사
                        for copy_idx in avalues_copy_indices:
                            if len(found_ref_chunk) > copy_idx and len(current_target_chunk) > copy_idx:
                                ref_value = found_ref_chunk[copy_idx]
                                
                                # 줄바꿈 태그 변환
                                if isinstance(ref_value, str):
                                    ref_value = ref_value.replace('\\n', '\n')

                                # 값 비교 및 업데이트
                                if modified_item["aValues"][i + copy_idx] != ref_value:
                                    modified_item["aValues"][i + copy_idx] = ref_value
                                    avalues_changes_in_chunk += 1
                                    changes_made_in_item = True
                                    # print(f"        [aValues 치환] '{os.path.basename(target_json_filepath)}' 항목 ID '{target_match_value}', 인덱스 {copy_idx} 값 업데이트.")
                                    
                                    # 중복 감지
                                    if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_translated_text']:
                                        _check_and_report_duplicates('Translated (aValues)', ref_value, target_json_filepath, duplicate_translated_texts, untranslated_items_report_data, original_text_for_translated=target_match_value)
                            else:
                                print(f"        [경고] '{os.path.basename(target_json_filepath)}' 항목 ID '{target_match_value}': 'aValues' 복사 인덱스 {copy_idx}가 범위 밖입니다. (타겟 청크:{len(current_target_chunk)}, 참조 청크:{len(found_ref_chunk)})")
                    else:
                        # 매칭되는 참조 청크를 찾지 못한 경우 (미번역 보고)
                        is_effectively_empty = (target_match_value == "" or target_match_value == "None")
                        if not (suppress_empty_untranslated_logs and is_effectively_empty):
                            display_match_key = target_match_value[:50] + ('...' if len(target_match_value) > 50 else '')
                            untranslated_items_report_data.append([
                                os.path.basename(target_json_filepath),
                                f'aValues (idx {avalues_match_idx})',
                                target_match_value,
                                '참조 JSON에 해당 aValues 매칭 키 없음',
                                ''
                            ])
                            print(f"        [미번역 발견] aValues (match_key): '{display_match_key}' (참조 JSON에 해당 매칭 키 없음) (보고서에 추가됨)")
                        # 중복 감지
                        if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text']:
                            _check_and_report_duplicates('Original (aValues)', target_match_value, target_json_filepath, duplicate_original_texts, untranslated_items_report_data)
                else:
                    print(f"        [경고] '{os.path.basename(target_json_filepath)}': 'aValues' 매칭 인덱스 {avalues_match_idx}가 청크 범위 밖입니다. (청크 길이: {len(current_target_chunk)})")
            
            if avalues_changes_in_chunk > 0:
                print(f"      [aValues 치환] '{os.path.basename(target_json_filepath)}'에서 {avalues_changes_in_chunk}개의 'aValues' 변경사항 적용.")

        elif target_field in modified_item and reference_field in reference_item:
            # === 일반 필드 치환 처리 ===
            target_value = modified_item[target_field]
            ref_value = reference_item[reference_field]

            # 줄바꿈 태그 변환
            if isinstance(ref_value, str):
                ref_value = ref_value.replace('\\n', '\n')

            if target_value != ref_value:
                modified_item[target_field] = ref_value
                changes_made_in_item = True
                print(f"        [일반 치환] '{os.path.basename(target_json_filepath)}' - 필드 '{target_field}' 값 업데이트.")
                
                # 중복 감지
                if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_translated_text']:
                    _check_and_report_duplicates('Translated', ref_value, target_json_filepath, duplicate_translated_texts, untranslated_items_report_data, original_text_for_translated=target_value)
        else:
            # 필드가 없거나 매칭되지 않는 경우 (aValues가 아니고 일반 필드인 경우)
            print(f"        [정보] '{os.path.basename(target_json_filepath)}': 필드 '{target_field}' 또는 '{reference_field}'가 타겟/참조 JSON 중 하나에 없습니다. 건너뜁니다.")
            # 중복 감지
            if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text'] and target_field in modified_item:
                _check_and_report_duplicates('Original', modified_item[target_field], target_json_filepath, duplicate_original_texts, untranslated_items_report_data)

    return changes_made_in_item

def perform_json_substitution(json_substitution_settings, json_input_directory_for_csv_processing,
                                use_custom_output_directory, output_json_directory,
                                suppress_empty_untranslated_logs):
    """
    json_substitution_settings에 정의된 규칙에 따라 여러 JSON 파일을 재귀적으로 탐색하여
    참조 JSON과 필드 값을 직접 치환 처리합니다.
    """
    print("\n===== JSON-to-JSON 치환 번역 시작 =====")
    
    # 이 함수에서 처리된 파일 목록을 CSV 처리 단계로 전달하여 중복 처리 방지
    substituted_json_files = set()

    if not json_substitution_settings['enable_substitution']:
        print("  [정보] JSON-to-JSON 치환 번역 기능이 비활성화되어 있습니다. 이 단계를 건너뜁니다.")
        return substituted_json_files

    if not json_substitution_settings['substitution_rules']:
        print("  [정보] 정의된 JSON-to-JSON 치환 규칙이 없습니다. 이 단계를 건너뜁니다.")
        return substituted_json_files

    for rule_idx, rule in enumerate(json_substitution_settings['substitution_rules']):
        if not rule.get('enabled', True):
            print(f"  [정보] 규칙 {rule_idx+1} '{rule.get('name', '')}'이(가) 비활성화되어 있습니다. 건너뜁니다.")
            continue

        target_root_dir = rule.get("target_root_directory")
        reference_root_dir = rule.get("reference_root_directory")
        file_patterns = rule.get("file_patterns", [])
        match_field = rule.get("match_field")
        substitution_fields = rule.get("substitution_fields", [])
        output_suffix = rule.get("output_suffix", "")

        if not target_root_dir or not os.path.isdir(target_root_dir):
            print(f"  [경고] 규칙 {rule_idx+1}: 대상 루트 디렉터리 '{target_root_dir}'를 찾을 수 없거나 유효하지 않습니다. 이 규칙을 건너뜁니다.")
            continue
        if not reference_root_dir or not os.path.isdir(reference_root_dir):
            print(f"  [경고] 규칙 {rule_idx+1}: 참조 루트 디렉터리 '{reference_root_dir}'를 찾을 수 없거나 유효하지 않습니다. 이 규칙을 건너뜁니다.")
            continue
        if not match_field:
            print(f"  [경고] 규칙 {rule_idx+1}: 'match_field'가 정의되지 않았습니다. 이 규칙을 건너뜁니다.")
            continue
        if not substitution_fields:
            print(f"  [경고] 규칙 {rule_idx+1}: 'substitution_fields'가 정의되지 않았습니다. 이 규칙을 건너뜁니다.")
            continue

        print(f"\n  --- 규칙 {rule_idx+1} '{rule.get('name', '')}' 적용 시작 ---")
        print(f"    대상 디렉터리: '{target_root_dir}'")
        print(f"    참조 디렉터리: '{reference_root_dir}'")
        print(f"    파일 패턴: {file_patterns if file_patterns else '모든 JSON 파일'}")
        print(f"    매칭 필드: '{match_field}'")

        target_json_files_in_rule = []
        try:
            for root, _, files in os.walk(target_root_dir):
                for file in files:
                    if file.lower().endswith('.json'):
                        if not file_patterns or file in file_patterns:
                            target_json_files_in_rule.append(os.path.join(root, file))
        except Exception as e:
            print(f"  [오류] 규칙 {rule_idx+1}: 대상 디렉터리 '{target_root_dir}' 탐색 중 오류 발생: {e}")
            continue

        if not target_json_files_in_rule:
            print(f"  [정보] 규칙 {rule_idx+1}: '{target_root_dir}'에서 치환할 JSON 파일을 찾을 수 없습니다.")
            continue
            
        print(f"  규칙 {rule_idx+1}에 따라 {len(target_json_files_in_rule)}개의 JSON 파일을 찾았습니다.")

        for i, target_json_filepath in enumerate(target_json_files_in_rule):
            print(f"\n    --- [{i+1}/{len(target_json_files_in_rule)}] '{os.path.basename(target_json_filepath)}' 치환 시도 ---")

            # 참조 JSON 파일 경로 결정: 대상 JSON의 상대 경로를 기준으로 참조 JSON 탐색
            try:
                relative_path_from_target_root = os.path.relpath(target_json_filepath, target_root_dir)
                reference_json_filepath = os.path.join(reference_root_dir, relative_path_from_target_root)
            except ValueError:
                print(f"      [경고] '{target_json_filepath}'의 상대 경로 계산 실패. 이 파일을 건너뜁니다.")
                continue

            if not os.path.exists(reference_json_filepath):
                print(f"      [경고] 매칭되는 참조 JSON 파일 '{reference_json_filepath}'을(를) 찾을 수 없습니다. 이 파일을 건너뜁니다.")
                continue

            # 출력 파일 경로 설정
            base_name, ext = os.path.splitext(os.path.basename(target_json_filepath))
            current_output_filename = f"{base_name}{output_suffix}{ext}"

            if use_custom_output_directory:
                # CSV 처리를 위한 json_input_directory_for_csv_processing를 기준으로 상대 경로 계산
                # 일관된 출력 디렉터리 구조 유지를 위함
                try:
                    relative_path_from_csv_input_root = os.path.relpath(target_json_filepath, json_input_directory_for_csv_processing)
                    output_dir_for_sub = os.path.join(output_json_directory, os.path.dirname(relative_path_from_csv_input_root))
                except ValueError:
                    print(f"      [경고] 대상 파일 '{target_json_filepath}'이(가) 일반 JSON 입력 디렉토리 '{json_input_directory_for_csv_processing}' 외부에 있습니다. 출력 파일은 '{output_json_directory}' 바로 아래에 저장됩니다.")
                    output_dir_for_sub = output_json_directory
                
                output_path_for_sub = os.path.join(output_dir_for_sub, current_output_filename)
            else:
                output_path_for_sub = os.path.join(os.path.dirname(target_json_filepath), current_output_filename)

            # JSON 파일 로드
            try:
                with open(target_json_filepath, 'r', encoding='utf-8') as f:
                    target_data = json.load(f)
                with open(reference_json_filepath, 'r', encoding='utf-8') as f:
                    reference_data = json.load(f)
            except Exception as e:
                print(f"      [오류] JSON 파일 로드 중 오류 발생: {e}. '{os.path.basename(target_json_filepath)}' 또는 '{os.path.basename(reference_json_filepath)}'")
                continue

            # 단일 객체 JSON도 리스트처럼 처리
            if not isinstance(target_data, list):
                target_data = [target_data]
            if not isinstance(reference_data, list):
                reference_data = [reference_data]

            # 참조 데이터를 match_field를 키로 하는 맵으로 변환
            reference_map = {item.get(match_field): item for item in reference_data if match_field in item}
            
            new_target_data = []
            changes_made = False

            for item_index, target_item in enumerate(target_data):
                modified_item = target_item.copy()
                
                # 매칭 필드 확인
                if match_field in target_item:
                    item_id = str(target_item[match_field])

                    # 중복 감지 (원본 텍스트)
                    if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text']:
                        _check_and_report_duplicates('Original', item_id, target_json_filepath, duplicate_original_texts, untranslated_items_report_data)

                    if item_id in reference_map:
                        reference_item = reference_map[item_id]
                        if _apply_substitution_to_item(modified_item, reference_item, substitution_fields, target_json_filepath, untranslated_items_report_data):
                            changes_made = True
                            print(f"      [아이템 치환] '{os.path.basename(target_json_filepath)}' 항목 ID '{item_id}'에서 변경사항 적용.")
                    else:
                        # 매칭되는 참조 아이템을 찾지 못한 경우 (미번역 보고)
                        is_effectively_empty = (item_id == "" or item_id == "None")
                        if not (suppress_empty_untranslated_logs and is_effectively_empty):
                            display_item_id = item_id[:50] + ('...' if len(item_id) > 50 else '')
                            untranslated_items_report_data.append([
                                os.path.basename(target_json_filepath),
                                f'Match Field: {match_field}',
                                item_id,
                                '참조 JSON에 해당 매칭 ID 없음',
                                ''
                            ])
                            print(f"      [미번역 발견] '{os.path.basename(target_json_filepath)}' 항목 ID '{display_item_id}' (참조 JSON에 ID 없음) (보고서에 추가됨)")
                else:
                    print(f"      [경고] '{os.path.basename(target_json_filepath)}' 항목 인덱스 {item_index}: 매칭 필드 '{match_field}'가 없어 치환을 건너뜁니다.")

                new_target_data.append(modified_item)

            if changes_made:
                try:
                    output_dir = os.path.dirname(output_path_for_sub)
                    if output_dir and not os.path.exists(output_dir):
                        os.makedirs(output_dir, exist_ok=True)
                        print(f"      하위 출력 디렉터리 '{output_dir}'를 생성했습니다.")

                    with open(output_path_for_sub, 'w', encoding='utf-8') as jsonfile:
                        json.dump(new_target_data, jsonfile, indent=4, ensure_ascii=False)
                    print(f"      JSON 파일 '{os.path.basename(output_path_for_sub)}'에 치환 변경사항이 성공적으로 저장되었습니다.")
                    substituted_json_files.add(os.path.abspath(target_json_filepath)) # 처리된 파일 목록에 추가
                except Exception as e:
                    print(f"      오류: JSON 파일 '{os.path.basename(output_path_for_sub)}' 쓰기 중 오류 발생: {e}")
            else:
                print(f"      JSON 파일 '{os.path.basename(target_json_filepath)}'에 치환할 내용이 없습니다.")
            print(f"    --- '{os.path.basename(target_json_filepath)}' 파일 치환 완료 ---")

    print("\n===== JSON-to-JSON 치환 번역 완료 =====")
    return substituted_json_files


def load_csv_to_translation_map(csv_path):
    """
    CSV 파일에서 번역 데이터를 로드하여 딕셔너리 형태로 반환합니다.
    CSV는 'JSON_Field_Name', 'Original Text', 'Translated Text' 세 개의 열을 가진다고 가정합니다.
    (헤더 없음)
    """
    # 중첩 딕셔너리 구조로 변경: {field_name: {original_text: translated_text}}
    translation_maps_by_field = {}

    if not os.path.exists(csv_path):
        print(f"경고: CSV 파일을 찾을 수 없습니다: '{csv_path}'. 이 파일에 대한 번역은 건너뜜니다.")
        return translation_maps_by_field

    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # 헤더 없이 바로 데이터 읽기
            for row_idx, row in enumerate(reader):
                # 최소 3개의 컬럼 (필드명, 원본, 번역)이 있다고 가정
                if len(row) < 3:
                    print(f"경고: CSV 파일 '{csv_path}'의 {row_idx + 1}번째 줄이 유효하지 않습니다. (최소 3개 컬럼 필요): {row}. 건너뜁니다.")
                    continue

                field_name = row[0] # 첫 번째 컬럼: JSON 필드 이름
                original_text = row[1] # 두 번째 컬럼: 원본 텍스트
                translated_text = row[2] # 세 번째 컬럼: 번역된 텍스트

                # 줄바꿈 태그 \n 또는 \n\n를 명시적으로 표시 (번역 결과에 명시적으로 표시)
                # CSV에서 읽어올 때 \\n을 \n으로 변환합니다.
                if isinstance(translated_text, str):
                    translated_text = translated_text.replace('\\n', '\n')

                # 해당 필드 이름에 대한 맵이 없으면 새로 생성
                if field_name not in translation_maps_by_field:
                    translation_maps_by_field[field_name] = {}

                # 해당 필드 맵에 번역 항목 추가
                translation_maps_by_field[field_name][original_text] = translated_text

        print(f"CSV 파일 '{csv_path}'에서 {len(translation_maps_by_field)}개의 필드에 대한 번역 데이터를 로드했습니다.")
        # 각 필드별 로드된 항목 수 출력 (옵션)
        # for field, t_map in translation_maps_by_field.items():
        #    print(f"  - 필드 '{field}': {len(t_map)}개 항목")

    except Exception as e:
        print(f"오류: CSV 파일 '{csv_path}' 로드 중 오류 발생: {e}")
    return translation_maps_by_field

def _convert_to_original_type(value):
    """
    값을 원본의 타입 (int, float, bool, str)으로 변환을 시도합니다.
    """
    if isinstance(value, str):
        # 정수로 변환 시도
        try:
            return int(value)
        except ValueError:
            pass
        # 부동 소수점으로 변환 시도
        try:
            return float(value)
        except ValueError:
            pass
        # 불리언으로 변환 시도
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
    return value # 변환 실패 시 원본 값 그대로 반환

def load_json_avalues_reference_data(search_root_dir, target_json_basename, match_idx):
    """
    지정된 루트 디렉토리와 그 하위 폴더에서 target_json_basename에 해당하는 JSON 파일을 찾아 로드하고,
    매칭 키를 기준으로 딕셔너리 형태로 반환합니다.
    """
    ref_data_map = {}
    found_file_path = None
    
    # search_root_dir 아래의 모든 하위 폴더를 재귀적으로 탐색합니다.
    for root, dirs, files in os.walk(search_root_dir):
        if target_json_basename in files:
            found_file_path = os.path.join(root, target_json_basename)
            break # 파일을 찾았으면 더 이상 탐색할 필요 없음

    if not found_file_path:
        print(f"경고: '{search_root_dir}' 및 하위 폴더에서 참조 JSON 파일 '{target_json_basename}'을(를) 찾을 수 없습니다. aValues 병합을 건너뜜니다.")
        return None # 파일 경로가 없으면 None 반환

    try:
        with open(found_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if "aValues" in item and isinstance(item["aValues"], list):
                        # 전역 설정 avalues_chunk_size 사용
                        for i in range(0, len(item["aValues"]), avalues_chunk_size):
                            chunk = item["aValues"][i : i + avalues_chunk_size]
                            if len(chunk) > match_idx:
                                # 매칭 키는 항상 문자열로 저장
                                key = str(chunk[match_idx])
                                # 각 청크 항목의 타입을 원본대로 유지하기 위해 변환 시도
                                typed_chunk = [_convert_to_original_type(val) for val in chunk]
                                ref_data_map[key] = typed_chunk # 전체 청크를 참조 데이터로 저장
            print(f"참조 JSON '{found_file_path}'에서 {len(ref_data_map)}개의 aValues 참조 항목을 로드했습니다.")
            return ref_data_map # 성공적으로 로드된 맵 반환
    except json.JSONDecodeError as e:
        print(f"오류: 참조 JSON 파일 '{found_file_path}' 파싱 중 오류 발생: {e}")
    except Exception as e:
        print(f"오류: 참조 JSON 파일 '{found_file_path}' 로드 중 오류 발생: {e}")
    return None # 오류 발생 시 None 반환
    
def _check_and_report_duplicates(text_type, text_content, json_filepath, report_dict, report_data_list, original_text_for_translated=None):
    """
    텍스트의 중복을 확인하고, 설정에 따라 보고서에 추가합니다.

    Args:
        text_type (str): 'Original' 또는 'Translated'.
        text_content (str): 중복을 확인할 텍스트 내용.
        json_filepath (str): 해당 텍스트가 발견된 JSON 파일의 경로.
        report_dict (dict): 중복 텍스트를 추적할 딕셔너리 (예: duplicate_original_texts).
        report_data_list (list): 미번역 보고서와 동일한 구조의 보고서 데이터를 수집할 리스트.
        original_text_for_translated (str, optional): 번역된 텍스트 중복을 확인할 경우, 해당 원본 텍스트.
    """
    # 사용자의 요청에 따라 모든 중복 감지 기능 비활성화
    if not OUTPUT_DUPLICATION_SETTINGS[f'detect_duplicate_{text_type.lower()}_text']:
        return

    if text_content is None or text_content == "":
        return

    # 정규화: 불필요한 공백과 줄바꿈을 단일 공백으로 치환하고 양쪽 끝 공백 제거
    normalized_text = re.sub(r'\s+', ' ', text_content).strip()
    if not normalized_text: # 정규화 후 비어있으면 중복 검사에서 제외
        return

    basename = os.path.basename(json_filepath)

    # 보고서에 추가될 항목 (기존 미번역 보고서 형식과 유사하게)
    report_entry = [
        basename,
        f'{text_type} Text (Duplicate)',
        text_content, # 원본 형태 유지
        f'{text_type} 텍스트 중복',
        # 번역 중복일 경우 원본 텍스트를 추가 정보로 제공
        original_text_for_translated if text_type == 'Translated' else ''
    ]

    # 중복 감지 및 보고 로직
    if normalized_text not in report_dict:
        report_dict[normalized_text] = {
            'files': {basename},
            'reported': False # 보고서에 추가되었는지 여부
        }
    else:
        # 이미 다른 파일에서 발견된 중복인 경우
        if basename not in report_dict[normalized_text]['files']:
            report_dict[normalized_text]['files'].add(basename)

            # report_duplicates_only_once가 False이거나, 아직 보고되지 않은 경우
            if not OUTPUT_DUPLICATION_SETTINGS['report_duplicates_only_once'] or not report_dict[normalized_text]['reported']:
                report_data_list.append(report_entry)
                report_dict[normalized_text]['reported'] = True # 보고됨으로 표시
                print(f"    [중복 발견] {text_type} 텍스트: '{normalized_text[:50]}...' (보고서에 추가됨)")
        # 같은 파일 내 중복은 현재 단계에서는 별도로 보고하지 않음 (의도적인 중복일 수 있음)


# ====================================================================================================================================
# === 2. 핵심 번역 및 처리 로직 함수 ===
# ====================================================================================================================================

# --- 2단계에서 추가될 헬퍼 함수 ---
def _process_string_field(modified_item, field_name, translations_map_for_all_fields, json_filepath, untranslated_report_data, suppress_empty_logs):
    """
    주어진 JSON 아이템의 특정 문자열 필드를 번역하고, 변경 여부를 추적하며,
    미번역 시 보고서 데이터를 추가합니다.
    `all_translations_by_field`는 이제 {field_name: {original: translated}} 형태의 중첩 딕셔너리입니다.
    """
    changes_made_in_field = False
    original_text = ""
    translated_text_final = None

    # 해당 필드에 대한 번역 맵 가져오기
    current_field_translations_map = translations_map_for_all_fields.get(field_name, {}) # 인자로 받은 변수를 사용

    # 필드 이름이 effective_fields_to_process에 포함되어 있는지 확인합니다.
    # (이는 translation_target_fields에 의해 채워집니다.)
    if field_name in modified_item and field_name in effective_fields_to_process:
        current_original = modified_item[field_name]
        if current_original is not None:
            original_text = str(current_original)
        else:
            original_text = "None"

        # --- 원본 텍스트 중복 감지 ---
        if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text']:
            _check_and_report_duplicates('Original', original_text, json_filepath, duplicate_original_texts, untranslated_report_data)

        if original_text in current_field_translations_map: # 해당 필드의 번역 맵에서 찾습니다.
            translated_text_final = current_field_translations_map[original_text]
            # 줄바꿈 태그는 load_csv_to_translation_map에서 이미 처리되었습니다.
            # 하지만 혹시 모를 경우를 대비해 한 번 더 확인 (안전장치)
            if isinstance(translated_text_final, str):
                translated_text_final = translated_text_final.replace('\\n', '\n') # 안전장치: CSV 로드 시 누락된 경우를 대비

            if modified_item[field_name] != translated_text_final:
                modified_item[field_name] = translated_text_final
                changes_made_in_field = True

                
        else:
            # 번역 맵에 없는 경우 원본 텍스트를 최종 번역 텍스트로 간주 (변경 없음)
            translated_text_final = original_text # 번역되지 않았으므로 원본 텍스트가 그대로 남아있을 것임

            report_reason = "CSV에 해당 원문 없음"
            matched_csv_original = ""
            normalized_json_original = re.sub(r'\s+', ' ', original_text).strip()

            # 공백/줄바꿈 차이로 매칭 실패한 경우 찾기
            # 해당 필드의 번역 맵(translations_map)에서만 확인
            for csv_original_key in current_field_translations_map.keys():
                normalized_csv_key = re.sub(r'\s+', ' ', csv_original_key).strip()
                if normalized_json_original == normalized_csv_key:
                    if original_text != csv_original_key:
                        report_reason = "CSV와 공백/줄바꿈 포함 여부가 다름"
                        matched_csv_original = csv_original_key
                    break

            is_effectively_empty = (original_text == "" or original_text == "None")

            if not (suppress_empty_logs and is_effectively_empty):
                display_text = original_text[:50] + ('...' if len(original_text) > 50 else '')
                untranslated_report_data.append([
                    os.path.basename(json_filepath),
                    field_name,
                    original_text,
                    report_reason,
                    matched_csv_original
                ])
                print(f"    [미번역 발견] {field_name}: '{display_text}' ({report_reason}) (보고서에 추가됨)")

    # --- 번역된 텍스트 중복 감지 (번역이 수행되었거나, 원본이 그대로 유지된 경우) ---
    if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_translated_text'] and translated_text_final is not None:
        _check_and_report_duplicates('Translated', translated_text_final, json_filepath, duplicate_translated_texts, untranslated_report_data, original_text_for_translated=original_text)

    return changes_made_in_field
    
    
def merge_json_with_reference(target_json_filepath, reference_json_filepath, output_filepath, fields_to_merge, id_field_name): # id_field_name 인자 추가
    """
    하나의 타겟 JSON 파일을 참조 JSON 파일과 병합합니다.
    주어진 필드들을 id_field를 기준으로 매칭하여 복사하거나,
    'aValues' 필드에 대한 특정 인덱스 기반 병합 규칙을 적용합니다.
    """
    print(f"'{os.path.basename(target_json_filepath)}' 파일을 참조 '{os.path.basename(reference_json_filepath)}'와 병합 시작...")

    try:
        with open(target_json_filepath, 'r', encoding='utf-8') as f:
            target_data = json.load(f)
        with open(reference_json_filepath, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)
    except FileNotFoundError as e:
        print(f"오류: 병합할 JSON 파일을 찾을 수 없습니다: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"오류: JSON 파일 파싱 중 오류 발생: {e}")
        return False
    except Exception as e:
        print(f"오류: JSON 파일 로드 중 오류 발생: {e}")
        return False

    changes_made = False
    new_target_data = []

    # 참조 데이터를 id_field 또는 aValues 매칭 키를 기준으로 빠르게 찾을 수 있도록 인덱싱
    # 이 부분은 merge_rules의 id_field 또는 avalues_merge_config에 따라 동적으로 구성되어야 합니다.
    # 현재는 fields_to_merge에 'aValues'가 있을 때만 특별 처리하므로,
    # 일반적인 id_field 매칭과 aValues 매칭을 분리하여 처리합니다.

    # === 'aValues' 특별 처리 로직 결정 ===
    # 해당 파일에 적용될 avalues_merge_config를 찾습니다.
    # json_direct_merge_settings['merge_rules']를 순회하며 현재 파일에 맞는 규칙을 찾습니다.
    current_avalues_merge_config = None
    for rule in json_direct_merge_settings.get('merge_rules', []):
        # 현재 처리 중인 target_json_filepath의 basename이 rule의 file_patterns에 포함되는지 확인
        target_basename_only = os.path.basename(target_json_filepath)
        if target_basename_only in rule.get('file_patterns', []):
            if 'aValues' in rule.get('fields_to_merge', []) and 'avalues_merge_config' in rule:
                current_avalues_merge_config = rule['avalues_merge_config']
                print(f"  [aValues 병합] '{target_basename_only}'에 대한 특정 'aValues' 병합 설정 적용.")
                break # 해당 파일에 맞는 규칙을 찾았으니 더 이상 탐색하지 않음
    # 참조 JSON 데이터 인덱싱
    # aValues 특별 처리가 아닌 일반 필드 병합일 경우 id_field로 인덱싱
    # aValues 특별 처리일 경우 reference_data를 그대로 사용 (내부에서 인덱싱)
    if current_avalues_merge_config:
        # aValues 병합 시에는 전체 reference_data를 사용하고, 내부에서 match_key_index로 각 item을 처리
        # 따라서 별도의 reference_map을 만들 필요는 없음
        print("  [aValues 병합] 참조 데이터를 'aValues' 인덱스 기반으로 처리 준비.")
        # 이 경우, ref_data_map은 전체 reference_data 리스트가 될 수 있음
        ref_data_map_for_lookup = reference_data
    elif id_field and id_field != "None": # 일반적인 id_field를 사용하는 경우
        ref_data_map_for_lookup = {}
        for ref_item in reference_data:
            if id_field in ref_item:
                ref_data_map_for_lookup[str(ref_item[id_field])] = ref_item
            else:
                print(f"  [경고] 참조 JSON에 ID 필드 '{id_field}'가 없는 항목이 있습니다: {ref_item}. 이 항목은 매칭되지 않습니다.")
        print(f"  [일반 병합] 참조 데이터를 ID 필드 '{id_field}' 기준으로 인덱싱 완료 ({len(ref_data_map_for_lookup)}개 항목).")
    else:
        print("  [정보] ID 필드가 지정되지 않았거나 'aValues' 특정 병합 설정이 없어 일반 필드 병합은 건너뜁니다.")
        ref_data_map_for_lookup = {} # 매칭할 데이터가 없음

    for item_index, target_item in enumerate(target_data):
        modified_item = target_item.copy()
        item_id_for_log = None # 로그용 ID

        # === 'aValues' 특별 병합 처리 ===
        if current_avalues_merge_config and "aValues" in modified_item and isinstance(modified_item["aValues"], list):
            avalues_match_idx = current_avalues_merge_config["match_key_index"]
            avalues_copy_indices = current_avalues_merge_config["copy_value_indices"]
            
            avalues_chunk_size_in_target = avalues_chunk_size # 이 변수는 전역이거나 다른 곳에서 정의되어야 합니다.
            # avalues_chunk_size가 정의되어 있지 않다면 기본값 설정 (예: 3)
            # if 'avalues_chunk_size' not in globals():
            #    avalues_chunk_size_in_target = 3
            
            avalues_changes_in_item = 0
            
            # target_item의 aValues 배열을 chunk_size에 따라 순회
            for i in range(0, len(modified_item["aValues"]), avalues_chunk_size_in_target):
                current_target_chunk = modified_item["aValues"][i : i + avalues_chunk_size_in_target]

                if len(current_target_chunk) > avalues_match_idx:
                    target_match_value = str(current_target_chunk[avalues_match_idx])

                    # 참조 데이터에서 매칭되는 'aValues' 청크 찾기
                    found_ref_chunk = None
                    for ref_json_item in ref_data_map_for_lookup: # ref_data_map_for_lookup은 현재 reference_data 리스트
                        if "aValues" in ref_json_item and isinstance(ref_json_item["aValues"], list):
                            for j in range(0, len(ref_json_item["aValues"]), avalues_chunk_size_in_target):
                                current_ref_chunk = ref_json_item["aValues"][j : j + avalues_chunk_size_in_target]
                                if len(current_ref_chunk) > avalues_match_idx and \
                                   str(current_ref_chunk[avalues_match_idx]) == target_match_value:
                                    found_ref_chunk = current_ref_chunk
                                    break
                            if found_ref_chunk:
                                break
                    
                    if found_ref_chunk:
                        # 매칭되는 청크를 찾았으면 지정된 인덱스의 값을 복사
                        for copy_idx in avalues_copy_indices:
                            if len(found_ref_chunk) > copy_idx and len(current_target_chunk) > copy_idx:
                                ref_value = found_ref_chunk[copy_idx]
                                
                                # 줄바꿈 태그 변환 (문자열인 경우)
                                if isinstance(ref_value, str):
                                    ref_value = ref_value.replace('\\n', '\n') # 원본과 동일하게 번역 결과에 명시적으로 표시 (저장 정보 반영)

                                # 값 비교 및 업데이트
                                if modified_item["aValues"][i + copy_idx] != ref_value:
                                    modified_item["aValues"][i + copy_idx] = ref_value
                                    avalues_changes_in_item += 1
                                    changes_made = True
                                    print(f"    [aValues 병합] '{os.path.basename(target_json_filepath)}' 항목 ID '{target_match_value}', 인덱스 {copy_idx} 값 업데이트.")
                                    
                                    # 중복 감지 (저장된 정보 반영)
                                    if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_translated_text']:
                                        _check_and_report_duplicates('Translated', ref_value, target_json_filepath, duplicate_translated_texts, untranslated_items_report_data, original_text_for_translated=target_match_value)
                            else:
                                print(f"    [경고] '{os.path.basename(target_json_filepath)}' 항목 ID '{target_match_value}': 'aValues' 복사 인덱스 {copy_idx}가 범위 밖입니다. (타겟 청크:{len(current_target_chunk)}, 참조 청크:{len(found_ref_chunk)})")
                    else:
                        # 매칭되는 참조 청크를 찾지 못한 경우 (미번역 보고)
                        is_effectively_empty = (target_match_value == "" or target_match_value == "None")
                        if not (suppress_empty_untranslated_logs and is_effectively_empty): # suppress_empty_untranslated_logs는 전역이거나 인자로 받아야 함
                            display_match_key = target_match_value[:50] + ('...' if len(target_match_value) > 50 else '')
                            untranslated_items_report_data.append([
                                os.path.basename(target_json_filepath),
                                f'aValues (idx {avalues_match_idx})', # 필드 타입
                                target_match_value,
                                '참조 JSON에 해당 aValues 매칭 키 없음',
                                ''
                            ])
                            print(f"    [미번역 발견] aValues (match_key): '{display_match_key}' (참조 JSON에 해당 매칭 키 없음) (보고서에 추가됨)")
                        # 중복 감지 (저장된 정보 반영)
                        if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text']:
                            _check_and_report_duplicates('Original', target_match_value, target_json_filepath, duplicate_original_texts, untranslated_items_report_data)
                else:
                    print(f"    [경고] '{os.path.basename(target_json_filepath)}' 항목 인덱스 {item_index}: 'aValues' 매칭 인덱스 {avalues_match_idx}가 청크 범위 밖입니다. (청크 길이: {len(current_target_chunk)})")

            if avalues_changes_in_item > 0:
                print(f"  [aValues 병합] '{os.path.basename(target_json_filepath)}' 항목 인덱스 {item_index}에서 {avalues_changes_in_item}개의 'aValues' 변경사항 적용.")
        
        # === 일반 필드 병합 처리 (aValues 특별 처리가 아닌 경우) ===
        # fields_to_merge에 'aValues'가 포함되어 있지 않거나,
        # 'aValues'가 포함되어 있더라도 current_avalues_merge_config가 없는 경우 (즉, 일반 aValues 필드처럼 처리)
        # 또는 'aValues'가 아닌 다른 필드를 병합하는 경우
        elif id_field and id_field != "None":
            if id_field in target_item:
                item_id = str(target_item[id_field])
                item_id_for_log = item_id # 로그용 ID 설정
                if item_id in ref_data_map_for_lookup:
                    ref_item = ref_data_map_for_lookup[item_id]
                    field_changes_in_item = 0
                    for field in fields_to_merge:
                        if field != "aValues": # 'aValues' 필드는 위에서 특별 처리했으므로 건너뜁니다.
                            if field in modified_item and field in ref_item:
                                target_value = modified_item[field]
                                ref_value = ref_item[field]

                                # 줄바꿈 태그 변환 (문자열인 경우)
                                if isinstance(ref_value, str):
                                    ref_value = ref_value.replace('\\n', '\n') # 원본과 동일하게 번역 결과에 명시적으로 표시 (저장 정보 반영)

                                if target_value != ref_value:
                                    modified_item[field] = ref_value
                                    changes_made = True
                                    field_changes_in_item += 1
                                    print(f"    [일반 병합] '{os.path.basename(target_json_filepath)}' 항목 ID '{item_id}' - 필드 '{field}' 값 업데이트.")
                                    
                                    # 중복 감지 (저장된 정보 반영)
                                    if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_translated_text']:
                                        _check_and_report_duplicates('Translated', ref_value, target_json_filepath, duplicate_translated_texts, untranslated_items_report_data, original_text_for_translated=target_value)
                            else:
                                # 필드가 없거나 매칭되지 않는 경우
                                print(f"    [정보] '{os.path.basename(target_json_filepath)}' 항목 ID '{item_id}': 필드 '{field}'가 타겟/참조 JSON 중 하나에 없습니다. 건너뜁니다.")
                                
                                # 중복 감지 (저장된 정보 반영)
                                if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text'] and field in modified_item:
                                    _check_and_report_duplicates('Original', modified_item[field], target_json_filepath, duplicate_original_texts, untranslated_items_report_data)

                    if field_changes_in_item > 0:
                        print(f"  [일반 병합] '{os.path.basename(target_json_filepath)}' 항목 ID '{item_id}'에서 {field_changes_in_item}개의 일반 필드 변경사항 적용.")
                else:
                    # ID가 참조 데이터에 없는 경우 (미번역 보고)
                    is_effectively_empty = (item_id == "" or item_id == "None")
                    if not (suppress_empty_untranslated_logs and is_effectively_empty): # suppress_empty_untranslated_logs는 전역이거나 인자로 받아야 함
                        display_item_id = item_id[:50] + ('...' if len(item_id) > 50 else '')
                        untranslated_items_report_data.append([
                            os.path.basename(target_json_filepath),
                            f'Field: {id_field}',
                            item_id,
                            '참조 JSON에 해당 ID 없음',
                            ''
                        ])
                        print(f"  [미번역 발견] '{os.path.basename(target_json_filepath)}' 항목 ID '{display_item_id}' (참조 JSON에 ID 없음) (보고서에 추가됨)")
                    # 중복 감지 (저장된 정보 반영)
                    if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text']:
                        _check_and_report_duplicates('Original', item_id, target_json_filepath, duplicate_original_texts, untranslated_items_report_data)
            else:
                # 타겟 JSON에 ID 필드가 없는 경우 (미번역 보고)
                # 이 경우는 조금 더 세부적인 로깅이 필요할 수 있습니다. 어떤 아이템인지 특정하기 어려움.
                print(f"  [경고] '{os.path.basename(target_json_filepath)}' 항목 인덱스 {item_index}: ID 필드 '{id_field}'가 없어 병합을 건너뜁니다.")

        new_target_data.append(modified_item)

    if changes_made:
        try:
            output_dir = os.path.dirname(output_json_filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"  하위 출력 디렉터리 '{output_dir}'를 생성했습니다.")

            with open(output_json_filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(new_target_data, jsonfile, indent=4, ensure_ascii=False)
            print(f"JSON 파일 '{os.path.basename(output_json_filepath)}'에 변경사항이 성공적으로 저장되었습니다.")
            return True
        except Exception as e:
            print(f"오류: JSON 파일 '{os.path.basename(output_json_filepath)}' 쓰기 중 오류 발생: {e}")
            return False
    else:
        print(f"JSON 파일 '{os.path.basename(target_json_filepath)}'에 변경할 내용이 없습니다.")
        return False


    # 리스트 형태의 JSON을 가정하고 처리
    # 단일 객체 JSON도 리스트처럼 처리할 수 있도록 만듭니다.
    if not isinstance(target_data, list):
        target_data = [target_data]
    if not isinstance(reference_data, list):
        reference_data = [reference_data]

    # id_field_name을 사용하여 참조 데이터를 맵으로 만듭니다.
    reference_map = {item.get(id_field_name): item for item in reference_data if id_field_name in item}

    merged_data = []
    for target_item in target_data:
        modified_item = target_item.copy()
        
        # 타겟 아이템에 id 필드가 있고, 참조 맵에 해당 id가 있는 경우
        if id_field_name in target_item and target_item[id_field_name] in reference_map:
            reference_item = reference_map[target_item[id_field_name]]
            for field in fields_to_merge:
                if field in reference_item and field in modified_item:
                    # 줄바꿈 태그 변환 (문자열인 경우)
                    ref_value = reference_item[field]
                    if isinstance(ref_value, str):
                        ref_value = ref_value.replace('\\n', '\n')

                    if modified_item[field] != ref_value:
                        modified_item[field] = ref_value
                        changes_made = True
                        # print(f"    필드 '{field}' 업데이트: '{target_item[field]}' -> '{ref_value}'") # 너무 많은 로그로 주석 처리
        merged_data.append(modified_item)

    if changes_made:
        try:
            output_dir = os.path.dirname(output_filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"하위 출력 디렉터리 '{output_dir}'를 생성했습니다.")

            with open(output_filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(merged_data, jsonfile, indent=4, ensure_ascii=False)
            print(f"JSON 파일 '{output_filepath}'에 병합된 변경사항이 성공적으로 저장되었습니다.")
            return True # 병합 성공 시 True 반환
        except Exception as e:
            print(f"오류: 병합된 JSON 파일 쓰기 중 오류 발생: {e}")
            return False # 병합 실패 시 False 반환
    else:
        print("JSON 파일에 병합할 내용이 없습니다.")
        return False # 변경 사항이 없으면 False 반환

    print(f"--- '{os.path.basename(target_json_filepath)}' 파일 병합 완료 ---")

def translate_json_file(json_filepath, csv_filepath, current_output_filepath, suppress_empty_untranslated_logs, json_input_directory=None):
    """
    단일 JSON 파일을 로드하고, CSV 번역 맵을 사용하여 지정된 필드를 번역합니다.
    번역된 내용은 새 파일로 저장하거나 원본 파일을 덮어쓸 수 있습니다.
    """
    print(f"'{os.path.basename(json_filepath)}' 파일 처리 시작...")

    json_base_name = os.path.basename(json_filepath)
    # 캐싱된 번역 맵 사용 또는 새로 로드
    # all_translations 변수는 이제 중첩 딕셔너리 {field: {original: translated}} 임
    if csv_filepath in loaded_translation_maps:
        all_translations_by_field = loaded_translation_maps[csv_filepath]
        print(f"    [CSV 로드] 캐싱된 CSV '{os.path.basename(csv_filepath)}' 사용.")
    else:
        all_translations_by_field = load_csv_to_translation_map(csv_filepath)
        if all_translations_by_field: # 빈 딕셔너리가 아니면 캐싱
            loaded_translation_maps[csv_filepath] = all_translations_by_field
        else:
            print(f"    [CSV 로드 실패] '{os.path.basename(csv_filepath)}'에서 유효한 번역 데이터를 로드할 수 없어 번역을 건너뜜니다.")
            print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")
            return

    # 전역 변수 effective_fields_to_process 설정:
    # 이제 CSV에서 로드된 필드 이름들을 기준으로 합니다.
    # 하지만 translation_target_fields도 여전히 유효하므로, 두 집합의 교집합을 사용하거나,
    # CSV에 있는 필드만 번역 대상으로 삼을 수 있습니다.
    # 여기서는 translation_target_fields에 정의된 필드만 처리하되, 해당 필드가 CSV에 존재해야 번역을 시도합니다.
    global effective_fields_to_process
    # translation_target_fields가 정의되어 있다면 해당 필드만 대상으로, 그렇지 않으면 CSV에 있는 모든 필드 대상으로
    if 'translation_target_fields' in globals() and translation_target_fields:
        effective_fields_to_process = [
            f for f in translation_target_fields
            if f in all_translations_by_field # CSV에 해당 필드 번역이 있는 경우만 포함
        ]
    else:
        # translation_target_fields가 없거나 비어있으면 CSV에 있는 모든 필드를 번역 대상으로
        effective_fields_to_process = list(all_translations_by_field.keys())

    if not effective_fields_to_process:
        print(f"    [정보] '{os.path.basename(json_filepath)}'에 대해 번역할 대상 필드가 없거나, CSV에 해당 필드 번역 데이터가 없습니다. 번역을 건너뜜니다.")
        print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")
        return


    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"오류: JSON 파일을 찾을 수 없습니다: '{json_filepath}'")
        print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")
        return
    except json.JSONDecodeError as e:
        print(f"오류: JSON 파일 '{json_filepath}' 파싱 중 오류 발생: {e}")
        print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")
        return
    except Exception as e:
        print(f"오류: JSON 파일 '{json_filepath}' 로드 중 오류 발생: {e}")
        print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")
        return

    new_json_data = []
    changes_made = False

    if not isinstance(data, list):
        data = [data]
        print(f"    [정보] 단일 JSON 객체를 리스트로 처리합니다.")

    for item_index, item in enumerate(data):
        modified_item = item.copy()

        # --- 문자열 필드 처리 (헬퍼 함수 호출) ---
        # 이제 all_translations_by_field 전체를 _process_string_field에 전달합니다.
        # _process_string_field 내부에서 field_name에 맞는 번역 맵을 가져올 것입니다.
        for field_name in effective_fields_to_process: # translation_target_fields 대신 effective_fields_to_process 사용
            if _process_string_field(modified_item, field_name, all_translations_by_field, json_filepath, untranslated_items_report_data, suppress_empty_untranslated_logs):
                changes_made = True

        # --- 'aValues' 필드 병합 처리 (이 부분은 변경 없음) ---
        # ... (기존 코드 유지) ...
        if json_avalues_merge_settings['merge_mode'] == 'specific_files':
            current_merge_config = None
            json_base_name_only = os.path.basename(json_filepath) # 파일명만 사용

            # 현재 JSON 파일에 대한 특정 병합 설정 찾기
            for config in json_avalues_merge_settings['specific_merge_configs']:
                if config['source_json_basename'] == json_base_name_only:
                    current_merge_config = config
                    break

            if current_merge_config:
                # ref_json_root_dir는 이제 탐색을 시작할 루트 디렉토리입니다.
                # (예: 'CSV')
                ref_json_root_dir = current_merge_config['reference_json_root_directory']
                match_idx = current_merge_config['match_key_index']
                copy_indices = current_merge_config['copy_value_indices']
                
                # 원본 JSON 파일의 이름 (확장자 포함)을 탐색 대상 이름으로 사용
                target_ref_basename = json_base_name_only 

                ref_data_for_current_json = None

                # 캐싱된 참조 데이터 확인
                # 캐시 키를 '{탐색루트}/{타겟파일명}' 형태로 변경하여 유니크하게 만듭니다.
                cache_key = os.path.join(ref_json_root_dir, target_ref_basename) 

                if cache_key in json_avalues_reference_data:
                    ref_data_for_current_json = json_avalues_reference_data[cache_key]
                    print(f"    [aValues 병합] 캐싱된 참조 JSON '{target_ref_basename}' 사용.")
                else:
                    # load_json_avalues_reference_data 함수가 이제 재귀 탐색을 수행합니다.
                    # potential_ref_json_path 대신 ref_json_root_dir와 target_ref_basename을 직접 전달합니다.
                    ref_data_for_current_json = load_json_avalues_reference_data(ref_json_root_dir, target_ref_basename, match_idx)
                    if ref_data_for_current_json is not None:
                        json_avalues_reference_data[cache_key] = ref_data_for_current_json
                    # 파일을 찾지 못했거나 로드에 실패한 경우는 load_json_avalues_reference_data 내부에서 경고를 출력합니다.

                if ref_data_for_current_json: # <--- 로드된 데이터가 있을 경우에만 병합 로직 실행
                    if "aValues" in modified_item and isinstance(modified_item["aValues"], list):
                        avalues_changes_count = 0

                        # avalues_chunk_size를 사용하여 반복
                        for i in range(0, len(modified_item["aValues"]), avalues_chunk_size):
                            current_avalues_chunk = modified_item["aValues"][i : i + avalues_chunk_size]

                            if len(current_avalues_chunk) > match_idx:
                                match_key_value = str(current_avalues_chunk[match_idx]) # 키는 문자열로 비교

                                # --- aValues 원본 값 중복 감지 ---
                                if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_original_text']:
                                    _check_and_report_duplicates('Original', match_key_value, json_filepath, duplicate_original_texts, untranslated_items_report_data)

                                if match_key_value in ref_data_for_current_json:
                                    ref_avalues_full_entry = ref_data_for_current_json[match_key_value]

                                    for copy_idx in copy_indices:
                                        if len(ref_avalues_full_entry) > copy_idx and len(current_avalues_chunk) > copy_idx:
                                            # 참조 JSON에서 가져온 값
                                            ref_value = ref_avalues_full_entry[copy_idx]

                                            # 현재 JSON에 있는 값
                                            current_item_value = modified_item["aValues"][i + copy_idx]

                                            # 줄바꿈 태그 변환 (문자열인 경우)
                                            if isinstance(ref_value, str):
                                                ref_value = ref_value.replace('\\n', '\n')

                                            # 값 비교 및 업데이트
                                            if current_item_value != ref_value:
                                                modified_item["aValues"][i + copy_idx] = ref_value
                                                avalues_changes_count += 1

                                            # --- aValues 번역/병합된 값 중복 감지 ---
                                            if OUTPUT_DUPLICATION_SETTINGS['detect_duplicate_translated_text']:
                                                _check_and_report_duplicates('Translated', ref_value, json_filepath, duplicate_translated_texts, untranslated_items_report_data, original_text_for_translated=str(match_key_value))
                                        else:
                                            print(f"    [경고] 'aValues' 병합: '{json_base_name_only}' - '{match_key_value}' 항목에서 복사 인덱스 {copy_idx}가 범위를 벗어났습니다. (원본:{len(current_avalues_chunk)}, 참조:{len(ref_avalues_full_entry)})")
                                else:
                                    is_effectively_empty = (match_key_value == "" or match_key_value == "None")
                                    if not (suppress_empty_untranslated_logs and is_effectively_empty):
                                        display_match_key = match_key_value[:50] + ('...' if len(match_key_value) > 50 else '')
                                        untranslated_items_report_data.append([
                                            os.path.basename(json_filepath),
                                            'aValues', # 필드 타입
                                            match_key_value,
                                            '참조 JSON에 해당 매칭 키 없음',
                                            ''
                                        ])
                                        print(f"    [미번역 발견] aValues (match_key): '{display_match_key}' (참조 JSON에 해당 매칭 키 없음) (보고서에 추가됨)")

                        if avalues_changes_count > 0:
                            changes_made = True

        new_json_data.append(modified_item)

    if changes_made:
        try:
            output_dir = os.path.dirname(current_output_filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"하위 출력 디렉터리 '{output_dir}'를 생성했습니다.")

            with open(current_output_filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(new_json_data, jsonfile, indent=4, ensure_ascii=False)
            print(f"JSON 파일 '{current_output_filepath}'에 변경사항이 성공적으로 저장되었습니다.")
        except Exception as e:
            print(f"JSON 파일 쓰기 중 오류 발생: {e}")
    else:
        print("JSON 파일에 변경할 내용이 없습니다.")

    print(f"--- '{os.path.basename(json_filepath)}' 파일 처리 완료 ---")
    

# ====================================================================================================================================
# === 다중 파일 처리 기능 ===
# ====================================================================================================================================

def process_multiple_json_files(json_input_directory, default_csv_filepath, save_output_to_new_file=True, output_suffix='_output', use_custom_output_directory=False, output_json_directory=None, match_csv_by_json=False, csv_root_for_matching=None, add_output_suffix=True, suppress_empty_untranslated_logs=False, processed_json_for_direct_merge=None): # 마지막에 추가
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
        suppress_empty_untranslated_logs (bool): 비어있는 미번역 로그를 억제할지 여부.
        processed_json_for_direct_merge (set): JSON-to-JSON 직접 병합으로 이미 처리된 파일들의 절대 경로 집합.
    """
    if processed_json_for_direct_merge is None:
        processed_json_for_direct_merge = set() # 기본값 설정

    print(f"\n===== '{json_input_directory}' 디렉터리 내 JSON 파일 처리 시작 =====")
    processed_files_count = 0 # 이 함수 내에서 사용할 카운터를 0으로 초기화

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
        json_file_absolute_path = os.path.abspath(json_filepath) # 절대 경로를 얻습니다.

        # JSON-to-JSON 직접 병합으로 처리된 파일은 건너뜁니다.
        if json_file_absolute_path in processed_json_for_direct_merge:
            print(f"\n--- [{i+1}/{len(json_files_found)}] 파일: {os.path.basename(json_filepath)} ---")
            print(f"    [정보] 이 파일은 JSON-to-JSON 직접 병합으로 이미 처리되었습니다. CSV 기반 번역을 건너뜁니다.")
            continue # 다음 파일로 넘어감


        print(f"\n--- [{i+1}/{len(json_files_found)}] 파일: {os.path.basename(json_filepath)} 처리 중 ---")

        # 사용할 CSV 파일 경로 결정
        current_csv_to_use = default_csv_filepath # 기본적으로는 기본 CSV를 사용
        if match_csv_by_json:
            json_base_name = os.path.splitext(os.path.basename(json_filepath))[0]

            found_matching_csv = False

            # 1. csv_root_for_matching에서 매칭 CSV 시도
            if csv_root_for_matching:
                # json_input_directory를 기준으로 JSON 파일의 상대 경로를 얻습니다.
                relative_path_from_json_root = os.path.relpath(json_filepath, json_input_directory)
                # 예: 'subdir/data.json' -> 'subdir/data.csv'
                potential_csv_path_in_root = os.path.join(csv_root_for_matching, relative_path_from_json_root.replace('.json', '.csv'))

                if os.path.exists(potential_csv_path_in_root):
                    current_csv_to_use = potential_csv_path_in_root
                    print(f"    [CSV 매칭] '{os.path.basename(json_filepath)}'에 대해 '{os.path.basename(potential_csv_path_in_root)}' (지정된 CSV 루트에서) 사용.")
                    found_matching_csv = True

            # 2. JSON 파일과 동일한 디렉터리에서 매칭 CSV 시도 (1번에서 찾지 못했을 경우)
            if not found_matching_csv:
                matching_csv_path_in_json_dir = os.path.join(os.path.dirname(json_filepath), f"{json_base_name}.csv")

                if os.path.exists(matching_csv_path_in_json_dir):
                    current_csv_to_use = matching_csv_path_in_json_dir
                    print(f"    [CSV 매칭] '{os.path.basename(json_filepath)}'에 대해 '{os.path.basename(matching_csv_path_in_json_dir)}' (JSON 파일과 동일 디렉터리에서) 사용.")
                    found_matching_csv = True

            # 3. 모든 매칭 시도 실패 시 기본 CSV 사용
            if not found_matching_csv:
                print(f"    [경고] '{os.path.basename(json_filepath)}'에 대한 매칭 CSV를 찾을 수 없습니다. 기본 CSV '{os.path.basename(default_csv_filepath)}'를 사용합니다.")
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

        # translate_json_file 호출 시 json_input_directory를 명시적으로 전달
        translate_json_file(json_filepath, current_csv_to_use, current_output_filepath, suppress_empty_untranslated_logs, json_input_directory)
        processed_files_count += 1
        print(f"--- '{os.path.basename(json_filepath)}' 처리 완료 ---")

# ====================================================================================================================================
# === JSON-to-JSON 다중 파일 직접 병합 기능 ===
# ====================================================================================================================================

def process_multiple_json_for_direct_merge(merge_rules, json_input_directory_for_csv_processing,
                                           use_custom_output_directory, output_json_directory,
                                           suppress_empty_untranslated_logs):
    """
    json_direct_merge_settings에 정의된 merge_rules에 따라 여러 JSON 파일을 재귀적으로 탐색하여
    참조 JSON과 직접 병합 처리합니다.
    
    Args:
        merge_rules (list): json_direct_merge_settings['merge_rules']에 정의된 병합 규칙 목록.
        json_input_directory_for_csv_processing (str): CSV 처리를 위한 JSON 입력 루트 디렉터리 (상대 경로 계산용).
        use_custom_output_directory (bool): True이면 output_json_directory에 계층 구조를 유지하며 저장.
        output_json_directory (str): 병합된 JSON 파일을 저장할 루트 디렉터리 경로.
        suppress_empty_untranslated_logs (bool): 비어있는 미번역 로그를 억제할지 여부.
    
    Returns:
        set: JSON-to-JSON 직접 병합으로 성공적으로 처리된 파일들의 절대 경로 집합.
    """
    print("\n===== JSON-to-JSON 직접 병합 (재귀 탐색) 시작 =====")
    processed_json_for_direct_merge_local = set()

    if not merge_rules:
        print("  [정보] 정의된 JSON-to-JSON 병합 규칙이 없습니다. 이 단계를 건너뜜니다.")
        return processed_json_for_direct_merge_local

    for rule_idx, rule in enumerate(merge_rules):
        target_root_dir = rule.get("target_root_directory")
        reference_root_dir = rule.get("reference_root_directory")
        file_patterns = rule.get("file_patterns", []) # 빈 리스트면 모든 JSON 파일
        fields_to_merge = rule.get("fields_to_merge", [])
        id_field = rule.get("id_field", "None") # 기본값 "None"
        output_suffix = rule.get("output_suffix", "")
        
        # avalues_merge_config는 merge_json_with_reference 함수 내에서 해당 rule을 참조하여 사용하도록 합니다.
        # 따라서 여기서는 별도로 추출하여 인자로 넘길 필요는 없습니다.

        if not target_root_dir or not os.path.isdir(target_root_dir):
            print(f"  [경고] 규칙 {rule_idx+1}: 대상 루트 디렉터리 '{target_root_dir}'를 찾을 수 없거나 유효하지 않습니다. 이 규칙을 건너뜁니다.")
            continue
        if not reference_root_dir or not os.path.isdir(reference_root_dir):
            print(f"  [경고] 규칙 {rule_idx+1}: 참조 루트 디렉터리 '{reference_root_dir}'를 찾을 수 없거나 유효하지 않습니다. 이 규칙을 건너뜀니다.")
            continue

        print(f"\n  --- 규칙 {rule_idx+1} 적용 시작 ---")
        print(f"    대상 디렉터리: '{target_root_dir}'")
        print(f"    참조 디렉터리: '{reference_root_dir}'")
        print(f"    파일 패턴: {file_patterns if file_patterns else '모든 JSON 파일'}")

        target_json_files_in_rule = []
        try:
            for root, _, files in os.walk(target_root_dir):
                for file in files:
                    if file.lower().endswith('.json'):
                        # 파일 패턴이 정의되어 있다면 패턴에 일치하는 파일만 포함
                        if not file_patterns or file in file_patterns:
                            target_json_files_in_rule.append(os.path.join(root, file))
        except Exception as e:
            print(f"  [오류] 규칙 {rule_idx+1}: 대상 디렉터리 '{target_root_dir}' 탐색 중 오류 발생: {e}")
            continue

        if not target_json_files_in_rule:
            print(f"  [정보] 규칙 {rule_idx+1}: '{target_root_dir}'에서 병합할 JSON 파일을 찾을 수 없습니다.")
            continue
            
        print(f"  규칙 {rule_idx+1}에 따라 {len(target_json_files_in_rule)}개의 JSON 파일을 찾았습니다.")

        for i, target_json_filepath in enumerate(target_json_files_in_rule):
            print(f"\n    --- [{i+1}/{len(target_json_files_in_rule)}] '{os.path.basename(target_json_filepath)}' 병합 시도 ---")

            # 참조 JSON 파일 경로 결정
            # target_json_filepath의 target_root_dir로부터의 상대 경로를 사용하여 reference_root_dir 내의 참조 파일 경로를 구성
            try:
                relative_path_from_target_root = os.path.relpath(target_json_filepath, target_root_dir)
                reference_json_filepath = os.path.join(reference_root_dir, relative_path_from_target_root)
            except ValueError:
                print(f"      [경고] '{target_json_filepath}'의 상대 경로 계산 실패. 이 파일을 건너뜁니다.")
                continue

            if not os.path.exists(reference_json_filepath):
                print(f"      [경고] 매칭되는 참조 JSON 파일 '{reference_json_filepath}'을(를) 찾을 수 없습니다. 이 파일을 건너뜁니다.")
                continue

            # 출력 파일 경로 설정
            base_name, ext = os.path.splitext(os.path.basename(target_json_filepath))
            current_output_filename = f"{base_name}{output_suffix}{ext}"

            if use_custom_output_directory:
                # json_input_directory_for_csv_processing (CSV 처리를 위한 최상위 영문 JSON 디렉토리)를 기준으로 상대 경로 계산
                # 이렇게 해야 CSV 처리 로직과 동일한 출력 디렉토리 구조를 유지할 수 있습니다.
                try:
                    relative_path_from_csv_input_root = os.path.relpath(target_json_filepath, json_input_directory_for_csv_processing)
                    output_dir_for_merge = os.path.join(output_json_directory, os.path.dirname(relative_path_from_csv_input_root))
                except ValueError:
                    # target_json_filepath가 json_input_directory_for_csv_processing 외부에 있다면
                    # output_json_directory 바로 아래에 저장되도록 처리
                    print(f"      [경고] 대상 파일 '{target_json_filepath}'이(가) 일반 JSON 입력 디렉토리 '{json_input_directory_for_csv_processing}' 외부에 있습니다. 출력 파일은 '{output_json_directory}' 바로 아래에 저장됩니다.")
                    output_dir_for_merge = output_json_directory
                
                output_path_for_merge = os.path.join(output_dir_for_merge, current_output_filename)
            else:
                # 원본 파일과 같은 디렉터리에 저장
                output_path_for_merge = os.path.join(os.path.dirname(target_json_filepath), current_output_filename)

            # 병합 함수 호출
            if merge_json_with_reference(target_json_filepath, reference_json_filepath, output_path_for_merge, fields_to_merge, id_field):
                processed_json_for_direct_merge_local.add(os.path.abspath(target_json_filepath))
                print(f"      [정보] '{os.path.basename(target_json_filepath)}' 직접 병합 완료 및 CSV 번역에서 제외 목록에 추가됨.")
            else:
                print(f"      [오류] '{os.path.basename(target_json_filepath)}' 직접 병합 실패 또는 변경 없음. (위의 로그 확인)")

    print("\n===== JSON-to-JSON 직접 병합 (재귀 탐색) 완료 =====")
    return processed_json_for_direct_merge_local
    
   
   
# ====================================================================================================================================
# === 스크립트 실행 시작 ===
# 모든 함수 정의가 끝난 후, 이 블록에서 스크립트의 메인 로직을 시작합니다.
# ====================================================================================================================================

if __name__ == "__main__":
    print("\n--- 스크립트 실행 시작 ---")

    # 커스텀 출력 루트 디렉터리 사용 시 최상위 폴더 생성
    if use_custom_output_directory and save_output_to_new_file_option:
        if not os.path.exists(output_json_directory):
            try:
                os.makedirs(output_json_directory, exist_ok=True)
                print(f"최상위 출력 디렉터리 '{output_json_directory}'를 생성했습니다.")
            except Exception as e:
                print(f"오류: 최상위 출력 디렉터리 '{output_json_directory}' 생성 실패: {e}")
                exit() # 디렉터리 생성 실패 시 스크립트 중단

    # JSON-to-JSON 직접 병합으로 처리된 파일 목록을 추적
    processed_json_for_direct_merge = set() 
    processed_json_files_for_skip_csv_translation = set()

    # --------------------------------------------------------------------------------------------------------------------------------
    # JSON-to-JSON 직접 병합 처리 시작 (재귀 탐색 함수 호출)
    # --------------------------------------------------------------------------------------------------------------------------------
    if json_direct_merge_settings['enable_direct_merge']:
        print("\n===== (기존) JSON-to-JSON 직접 병합 처리 시작 =====")
        # process_multiple_json_for_direct_merge 함수 호출
        # 이 함수의 반환값은 이미 처리된 파일들의 절대 경로 집합입니다.
        processed_json_files_for_skip_csv_translation.update(
            process_multiple_json_for_direct_merge(
                json_direct_merge_settings['merge_rules'],
                json_input_directory, # CSV 처리를 위한 JSON 입력 루트 디렉터리 (상대 경로 계산용)
                use_custom_output_directory,
                output_json_directory,
                suppress_empty_untranslated_logs
            )
        )
        print("===== (기존) JSON-to-JSON 직접 병합 처리 완료 =====")
    # --------------------------------------------------------------------------------------------------------------------------------
    # --------------------------------------------------------------------------------------------------------------------------------
    # JSON-to-JSON 치환 번역 처리 시작 (새로운 로직 추가)
    # --------------------------------------------------------------------------------------------------------------------------------
    if json_substitution_settings['enable_substitution']:
        print("\n===== (새로운) JSON-to-JSON 치환 번역 처리 시작 =====")
        # perform_json_substitution 함수 호출
        # 이 함수의 반환값 역시 처리된 파일들의 절대 경로 집합입니다.
        processed_json_files_for_skip_csv_translation.update(
            perform_json_substitution(
                json_substitution_settings,
                json_input_directory, # CSV 처리를 위한 JSON 입력 루트 디렉터리 (상대 경로 계산용)
                use_custom_output_directory,
                output_json_directory,
                suppress_empty_untranslated_logs
            )
        )
        print("===== (새로운) JSON-to-JSON 치환 번역 처리 완료 =====")
    # --------------------------------------------------------------------------------------------------------------------------------

    # CSV 기반 번역 로직 실행
    if process_all_files_in_directory:
        # process_multiple_json_files 함수에 이미 직접 병합된 파일 목록을 전달하여 건너뛰도록 함
        process_multiple_json_files(json_input_directory, csv_file_path, # csv_file_path를 default_csv_filepath로 전달
                                     save_output_to_new_file_option, output_file_suffix,
                                     use_custom_output_directory, output_json_directory,
                                     match_csv_by_json_filename, csv_root_directory_for_matching, add_output_suffix,
                                     suppress_empty_untranslated_logs, processed_json_for_direct_merge)
    else:
        # 단일 파일 처리 시, 해당 파일이 JSON-to-JSON 직접 병합으로 처리되지 않은 경우에만 CSV 번역 시도
        json_file_absolute_path = os.path.abspath(json_single_file_name) # 단일 파일의 절대 경로를 미리 얻어둡니다.

        if json_file_absolute_path in processed_json_for_direct_merge:
            print(f"\n--- '{os.path.basename(json_single_file_name)}' 파일 처리 ---")
            print(f"정보: '{os.path.basename(json_single_file_name)}' 파일은 JSON-to-JSON 직접 병합으로 이미 처리되었습니다. CSV 기반 번역을 건너뜁니다.")
        else:
            # 단일 파일 모드일 때도 json_input_directory와 유사한 역할을 할 기준 디렉토리를 설정합니다.
            # json_single_file_name이 상대 경로일 경우를 대비하여 os.path.dirname(json_file_absolute_path)를 사용합니다.
            # 이렇게 하면 _process_string_field 함수 내부에서 json_input_directory가 None이 아니게 되어
            # 상대 경로 계산이 좀 더 견고해집니다.
            # 'json_input_directory' 대신 이 경우에 사용할 루트 디렉터리를 명확히 전달합니다.
            single_file_base_dir = os.path.dirname(json_file_absolute_path) if os.path.dirname(json_file_absolute_path) else os.getcwd()

            # 사용할 CSV 파일 경로 결정 (단일 파일 모드)
            current_csv_to_use = csv_file_path # 기본적으로는 기본 CSV를 사용
            if match_csv_by_json_filename:
                json_base_name = os.path.splitext(os.path.basename(json_single_file_name))[0]
                found_matching_csv = False

                # 1. csv_root_directory_for_matching에서 매칭 CSV 시도
                if csv_root_directory_for_matching and os.path.isdir(csv_root_directory_for_matching):
                    # 단일 파일의 상대 경로 계산 (single_file_base_dir 기준)
                    relative_path_from_single_file_base = os.path.relpath(json_file_absolute_path, single_file_base_dir)
                    potential_csv_path_in_root = os.path.join(csv_root_directory_for_matching, relative_path_from_single_file_base.replace('.json', '.csv'))

                    if os.path.exists(potential_csv_path_in_root):
                        current_csv_to_use = potential_csv_path_in_root
                        print(f"  [CSV 매칭] '{os.path.basename(json_single_file_name)}'에 대해 '{os.path.basename(potential_csv_path_in_root)}' (지정된 CSV 루트에서) 사용.")
                        found_matching_csv = True

                # 2. JSON 파일과 동일한 디렉터리에서 매칭 CSV 시도 (1번에서 찾지 못했을 경우)
                if not found_matching_csv:
                    # os.path.dirname(json_file_absolute_path)를 사용하여 정확한 디렉토리를 가져옴
                    matching_csv_path_in_json_dir = os.path.join(os.path.dirname(json_file_absolute_path), f"{json_base_name}.csv")

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
                    # single_file_base_dir를 기준으로 상대 경로 계산
                    relative_input_subdir = os.path.relpath(os.path.dirname(json_file_absolute_path), single_file_base_dir)
                    output_target_filepath = os.path.join(output_json_directory, relative_input_subdir, current_output_filename)
                else:
                    input_file_dir = os.path.dirname(json_file_absolute_path)
                    if not input_file_dir:
                        input_file_dir = '.'
                    output_target_filepath = os.path.join(input_file_dir, current_output_filename)
            else:
                output_target_filepath = json_file_absolute_path # 절대 경로를 사용

            # 마지막으로 `translate_json_file` 호출:
            # 단일 파일 처리 시, json_input_directory 역할에 single_file_base_dir를 전달합니다.
            translate_json_file(json_file_absolute_path, current_csv_to_use, output_target_filepath, suppress_empty_untranslated_logs, single_file_base_dir)


    # --- 미번역 항목 보고서 생성 (모든 JSON 파일 처리 완료 후) ---
    if generate_untranslated_report:
        # 미번역 항목 또는 중복 항목이 있을 경우
        if untranslated_items_report_data:
            print(f"\n--- 보고서 생성 중: '{untranslated_report_filename}' ---")
            try:
                with open(untranslated_report_filename, 'w', newline='', encoding='utf-8') as report_file:
                    report_writer = csv.writer(report_file)
                    # CSV 헤더 작성: 변경된 데이터 구조에 맞춰 헤더 추가
                    report_writer.writerow([
                        'JSON File Path',
                        'Field Type', # 'strName', 'aValues', 'Original Text (Duplicate)', 'Translated Text (Duplicate)' 등
                        'Original Text (from JSON)', # 실제 원본 텍스트 (길 경우 잘릴 수 있음)
                        'Reason/Status', # 미번역 이유 또는 중복 상태
                        'Matching CSV Original Text / Original Text for Translated Duplicate' # 추가 정보
                    ])
                    # 수집된 데이터 쓰기
                    for item_info in untranslated_items_report_data:
                        report_writer.writerow(item_info)
                print("보고서가 성공적으로 생성되었습니다.")
            except Exception as e:
                print(f"오류: 보고서 생성 중 오류 발생: {e}")
        else: # 수집된 데이터가 없을 경우 (미번역 및 중복 없음)
            print("정보: 모든 항목이 번역되었거나, 보고할 중복 항목이 없으므로 보고서 파일이 생성되지 않습니다.")

    print("\n--- 전체 스크립트 실행 종료 ---")