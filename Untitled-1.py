import streamlit as st
import pandas as pd
import os
import io
import re
from datetime import datetime

# 데이터를 저장할 파일 이름
CSV_FILE = 'import_materials.csv'

def load_data():
    """데이터 파일을 읽어오거나, 없으면 초기 샘플 데이터를 생성합니다."""
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        
        # PO 번호를 항상 문자열(글자)로 취급하여 숫자/글자 인식 오류를 방지합니다.
        df['PO 번호'] = df['PO 번호'].astype(str)

        # 기존 CSV 파일에 새 체크박스 열이 없으면 추가해 줍니다.
        for col in ['PO 송부', 'SC수령', 'IL 승인', '성적서', '선적서류']:
            if col not in df.columns:
                df[col] = False
        df[['PO 송부', 'SC수령', 'IL 승인', '성적서', '선적서류']] = df[['PO 송부', 'SC수령', 'IL 승인', '성적서', '선적서류']].fillna(False).astype(bool)
        
        # 선적일자 열이 없으면 빈 텍스트로 추가합니다.
        if '선적일자' not in df.columns:
            df['선적일자'] = ""
        df['선적일자'] = df['선적일자'].fillna("").astype(str)
        
        # 비고 열이 없으면 빈 텍스트로 추가합니다.
        if '비고' not in df.columns:
            df['비고'] = ""
        df['비고'] = df['비고'].fillna("").astype(str)

        # PO 파일 열이 없으면 빈 텍스트로 추가합니다.
        if 'PO 파일' not in df.columns:
            df['PO 파일'] = ""
        df['PO 파일'] = df['PO 파일'].fillna("").astype(str)
        return df
    else:
        return pd.DataFrame([
            {'PO 번호': 'PO-2023-001', '원료명': '아세트아미노펜', '수량': '1000 kg', '가격': 'USD 5,000', '제조원': 'Pharma Inc.', '공급원': 'Global Chem', '비고': '', 'PO 송부': False, 'PO 파일': '', 'SC수령': False, 'IL 승인': False, '선적일자': '', '성적서': False, '선적서류': False},
            {'PO 번호': 'PO-2023-002', '원료명': '이부프로펜', '수량': '500 kg', '가격': 'USD 3,200', '제조원': 'MediCore', '공급원': 'Global Chem', '비고': '', 'PO 송부': False, 'PO 파일': '', 'SC수령': False, 'IL 승인': False, '선적일자': '', '성적서': False, '선적서류': False},
            {'PO 번호': 'PO-2023-003', '원료명': '시트르산', '수량': '2000 kg', '가격': 'USD 4,500', '제조원': 'BioSource', '공급원': 'ChemTrade', '비고': '', 'PO 송부': False, 'PO 파일': '', 'SC수령': False, 'IL 승인': False, '선적일자': '', '성적서': False, '선적서류': False},
        ])

def clean_to_number(val):
    """문자열에서 단위와 쉼표를 제거하고 숫자만 추출합니다."""
    if pd.isna(val):
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def format_date_input(date_str):
    """'월/일' 또는 '월-일' 형식의 입력을 'YYYY-MM-DD' 형식으로 자동 변환합니다."""
    date_str = str(date_str).strip()
    if not date_str:
        return ""
    
    # 1/22, 01-22 등의 패턴 확인
    if re.match(r'^\d{1,2}[/-]\d{1,2}$', date_str):
        try:
            month, day = date_str.replace('-', '/').split('/')
            current_year = datetime.now().year # 현재 연도를 자동으로 가져옵니다.
            return f"{current_year}-{int(month):02d}-{int(day):02d}"
        except ValueError:
            return date_str
    return date_str

def main():
    st.set_page_config(page_title="수입 원료 관리", layout="wide")
    st.title("💊 ABP 수입 원료 관리 시스템")

    # 데이터 불러오기
    df = load_data()

    # 수량 데이터 포맷팅: 숫자와 kg 사이에 띄어쓰기를 넣고, kg은 소문자로 변환
    df['수량'] = df['수량'].apply(lambda x: re.sub(r'(?i)([\d.,]+)\s*kg', r'\1 kg', str(x)) if pd.notna(x) else x)

    # 탭을 사용하여 화면 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 목록 보기", "➕ 내역 추가", "🗑️ 내역 삭제", "✏️ 내역 수정", " 데이터 업로드", "📈 대시보드"])

    with tab1:
        st.subheader("현재 관리 중인 원료 목록")

        # --- 검색 기능 UI ---
        col1, col2 = st.columns(2)
        with col1:
            search_option = st.selectbox("검색할 항목 선택", ("원료명", "공급원"))
        with col2:
            search_term = st.text_input("검색어 입력")

        show_completed_only = st.checkbox("✅ 모든 진행 상태가 완료(체크)된 항목만 보기")

        sort_order = st.radio("🗓️ 선적일자 정렬", ["기본", "오름차순 (과거 날짜 먼저)", "내림차순 (최신 날짜 먼저)"], horizontal=True)

        # --- 데이터 필터링 로직 ---
        if search_term:
            # 'str.contains'를 사용하여 해당 검색어를 포함하는 행을 찾습니다 (대소문자 구분 안함).
            filtered_df = df[df[search_option].str.contains(search_term, case=False, na=False)].copy()
        else:
            filtered_df = df.copy()

        # 모든 진행 상태가 True(체크됨)인 항목만 필터링
        if show_completed_only:
            filtered_df = filtered_df[filtered_df['PO 송부'] & filtered_df['SC수령'] & filtered_df['IL 승인'] & filtered_df['성적서'] & filtered_df['선적서류']]

        # --- 선적일자 정렬 로직 ---
        if sort_order == "오름차순 (과거 날짜 먼저)":
            # 빈칸인 데이터는 맨 아래로 가도록 임시로 아주 먼 미래 날짜로 치환하여 정렬합니다.
            filtered_df['_sort_key'] = filtered_df['선적일자'].replace('', '9999-12-31')
            filtered_df = filtered_df.sort_values('_sort_key', ascending=True).drop(columns=['_sort_key'])
        elif sort_order == "내림차순 (최신 날짜 먼저)":
            # 빈칸인 데이터는 맨 아래로 가도록 임시로 아주 옛날 날짜로 치환하여 정렬합니다.
            filtered_df['_sort_key'] = filtered_df['선적일자'].replace('', '0000-00-00')
            filtered_df = filtered_df.sort_values('_sort_key', ascending=False).drop(columns=['_sort_key'])

        # --- 총 금액 계산 및 열 추가 ---
        qty_num = filtered_df['수량'].apply(clean_to_number)
        price_num = filtered_df['가격'].apply(clean_to_number)
        # 수량 * 가격을 계산하고 천 단위 쉼표를 넣어 보기 좋게 포맷팅합니다.
        filtered_df['총 금액'] = (qty_num * price_num).apply(lambda x: f"{x:,.2f}".rstrip('0').rstrip('.'))

        # 열 순서 변경 (표에서는 'PO 파일' 칸을 숨기고 'PO 송부' 칸 하나만 깔끔하게 남김)
        filtered_df = filtered_df[['PO 번호', '원료명', '수량', '가격', '총 금액', '제조원', '공급원', '비고', 'PO 송부', 'SC수령', 'IL 승인', '선적일자', '성적서', '선적서류']]

        # 데이터 에디터로 표시하여 사용자가 체크박스를 직접 클릭해서 수정할 수 있게 함
        edited_df = st.data_editor(
            filtered_df,
            use_container_width=True,
            disabled=['PO 번호', '원료명', '수량', '가격', '총 금액', '제조원', '공급원', '비고'], # 읽기 전용 잠금 (비고는 수정 탭에서)
            hide_index=True
        )

        # 사용자가 체크박스를 클릭해서 변경사항이 발생했는지 감지하고 즉시 자동 저장
        status_changed = False
        for index, row in edited_df.iterrows():
            # 에러 방지: 무조건 문자로 변환하여 비교하고, 찾지 못하면 건너뜁니다.
            po = str(row['PO 번호'])
            mask = df['PO 번호'].astype(str) == po
            
            if df[mask].empty:
                continue
                
            orig_row = df[mask].iloc[0]
            # 체크박스 상태나 선적일자 텍스트가 하나라도 변경되었다면 감지
            if (bool(orig_row['PO 송부']) != bool(row['PO 송부']) or bool(orig_row['SC수령']) != bool(row['SC수령']) or 
                bool(orig_row['IL 승인']) != bool(row['IL 승인']) or str(orig_row['선적일자']) != str(row['선적일자']) or
                bool(orig_row['성적서']) != bool(row['성적서']) or bool(orig_row['선적서류']) != bool(row['선적서류'])):
                
                formatted_date = format_date_input(row['선적일자'])
                df.loc[mask, ['PO 송부', 'SC수령', 'IL 승인', '선적일자', '성적서', '선적서류']] = [bool(row['PO 송부']), bool(row['SC수령']), bool(row['IL 승인']), formatted_date, bool(row['성적서']), bool(row['선적서류'])]
                status_changed = True
        
        if status_changed:
            df.to_csv(CSV_FILE, index=False)
            st.rerun()

        # --- 매우 심플한 PO 파일 첨부 및 다운로드 UI ---
        st.markdown("##### 📎 PO 파일 첨부 및 다운로드")
        
        if not filtered_df.empty:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                # 현재 목록에 있는 PO 번호 중 하나를 선택
                selected_po = st.selectbox("PO 번호 선택", filtered_df['PO 번호'].unique(), key="po_file_select")
            
            if selected_po:
                os.makedirs("attachments", exist_ok=True) # 폴더 자동 생성
                file_path = os.path.join("attachments", f"{selected_po}_PO.pdf")
                file_exists = os.path.exists(file_path)
                
                with c2:
                    if not file_exists:
                        uploaded_file = st.file_uploader("여기에 PDF 파일을 올려주세요", type=['pdf'], label_visibility="collapsed")
                        if uploaded_file:
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            df.loc[df['PO 번호'] == selected_po, 'PO 파일'] = "O"
                            df.to_csv(CSV_FILE, index=False)
                            st.rerun()
                    else:
                        st.success("✅ 파일이 첨부되어 있습니다.")
                        
                with c3:
                    if file_exists:
                        with open(file_path, "rb") as f:
                            st.download_button("📥 다운로드", f, file_name=f"{selected_po}_PO.pdf", mime="application/pdf", use_container_width=True)
                        if st.button("🗑️ 삭제", use_container_width=True):
                            os.remove(file_path)
                            df.loc[df['PO 번호'] == selected_po, 'PO 파일'] = ""
                            df.to_csv(CSV_FILE, index=False)
                            st.rerun()

        # --- 총합계 계산 및 표시 ---
        total_qty = filtered_df['수량'].apply(clean_to_number).sum()
        total_price = filtered_df['가격'].apply(clean_to_number).sum()

        st.markdown("#### 📊 요약 정보 (현재 목록 기준)")
        sum_col1, sum_col2 = st.columns(2)
        sum_col1.metric("총 수량", f"{total_qty:,.2f}".rstrip('0').rstrip('.'))
        sum_col2.metric("총 가격", f"{total_price:,.2f}".rstrip('0').rstrip('.'))
        
        st.divider() # 시각적 분리선 추가

        # 엑셀 다운로드 버튼
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
            
        st.download_button(
            label="📥 엑셀 파일로 다운로드",
            data=buffer.getvalue(),
            file_name="import_materials.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tab2:
        st.subheader("새로운 구매 내역 입력")
        # 입력 폼 생성
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                po = st.text_input("PO 번호")
                name = st.text_input("원료명")
                
                # 수량 입력 (숫자 + 단위)
                q_col1, q_col2 = st.columns([2, 1])
                with q_col1:
                    qty_val = st.text_input("수량 (숫자)")
                with q_col2:
                    qty_unit = st.selectbox("수량 단위", ["kg", "G", "L", "ML", "EA"])
            with col2:
                # 가격 입력 (통화 + 숫자)
                p_col1, p_col2 = st.columns([1, 2])
                with p_col1:
                    price_unit = st.selectbox("통화 단위", ["USD", "KRW", "EUR", "JPY"])
                with p_col2:
                    price_val = st.text_input("가격 (숫자)")
                    
                maker = st.text_input("제조원")
                supplier = st.text_input("공급원")
            
            memo = st.text_input("비고 (메모)")
            
            submitted = st.form_submit_button("저장하기")
            
            if submitted:
                final_qty = f"{qty_val} {qty_unit}" if qty_val else ""
                final_price = f"{price_unit} {price_val}" if price_val else ""
                new_data = pd.DataFrame([{'PO 번호': po, '원료명': name, '수량': final_qty, '가격': final_price, '제조원': maker, '공급원': supplier, '비고': memo, 'PO 송부': False, 'PO 파일': '', 'SC수령': False, 'IL 승인': False, '선적일자': '', '성적서': False, '선적서류': False}])
                # 기존 데이터에 합치고 파일로 저장
                updated_df = pd.concat([df, new_data], ignore_index=True)
                updated_df.to_csv(CSV_FILE, index=False)
                st.success("데이터가 저장되었습니다! '목록 보기' 탭을 눌러 확인해보세요.")

    with tab3:
        st.subheader("구매 내역 삭제")
        
        if not df.empty:
            # 삭제할 PO 번호 선택 (다중 선택 가능)
            selected_delete = st.multiselect("삭제할 PO 번호를 선택하세요", df['PO 번호'].unique())
            
            if st.button("선택한 내역 삭제"):
                if selected_delete:
                    # 선택된 PO 번호를 제외하고 다시 저장
                    new_df = df[~df['PO 번호'].isin(selected_delete)]
                    new_df.to_csv(CSV_FILE, index=False)
                    st.success("삭제되었습니다.")
                    st.rerun()
                else:
                    st.warning("삭제할 항목을 선택해주세요.")
        else:
            st.info("삭제할 데이터가 없습니다.")

    with tab5:
        st.subheader("엑셀/CSV 파일 대량 업로드")
        st.info("💡 업로드할 파일의 첫 번째 줄(헤더)은 반드시 **'PO 번호', '원료명', '수량', '가격', '총 금액', '제조원', '공급원'** 이어야 합니다. (선택 추가: '선적일자')")

        uploaded_file = st.file_uploader("파일을 드래그하거나 선택하세요 (.xlsx, .csv)", type=['xlsx', 'csv'])
        
        if uploaded_file is not None:
            try:
                # 파일 확장자에 따라 다르게 읽기
                if uploaded_file.name.endswith('.csv'):
                    upload_df = pd.read_csv(uploaded_file)
                else:
                    upload_df = pd.read_excel(uploaded_file)
                
                # 열 이름에 포함된 앞뒤 공백(띄어쓰기)을 제거하여 인식 오류 방지
                upload_df.columns = upload_df.columns.str.strip()

                # 필수 열 확인 ('총 금액'은 앱에서 자동 계산하므로 없어도 허용되게 유연하게 변경)
                base_cols = ['PO 번호', '원료명', '수량', '가격', '제조원', '공급원']
                if all(col in upload_df.columns for col in base_cols):
                    optional_cols = [col for col in ['총 금액', '선적일자', '비고'] if col in upload_df.columns]
                    cols_to_extract = base_cols + optional_cols
                    st.write("미리보기:")
                    st.dataframe(upload_df[cols_to_extract].head()) # 데이터 미리보기
                    
                    if st.button("이 데이터를 기존 목록에 추가/업데이트하기"):
                        # 업로드된 데이터에 선적일자가 있다면 날짜 자동 변환(포맷팅) 적용
                        if '선적일자' in upload_df.columns:
                            upload_df['선적일자'] = upload_df['선적일자'].apply(format_date_input)
                            
                        upload_data = upload_df[cols_to_extract].copy()
                        upload_data['PO 번호'] = upload_data['PO 번호'].astype(str)
                        # 업로드 파일 내에 중복 PO가 있을 경우 맨 마지막 데이터만 적용
                        upload_data = upload_data.drop_duplicates(subset=['PO 번호'], keep='last')
                        
                        df_indexed = df.set_index('PO 번호')
                        upload_indexed = upload_data.set_index('PO 번호')
                        
                        # 1. 기존 데이터 덮어쓰기 (체크박스 상태 등은 보존됨)
                        df_indexed.update(upload_indexed)
                        
                        # 2. 완전히 새로운 PO 번호만 목록 맨 아래에 추가
                        new_rows = upload_indexed[~upload_indexed.index.isin(df_indexed.index)]
                        updated_df = pd.concat([df_indexed, new_rows]).reset_index()
                        
                        # 열 순서를 기존 목록과 동일하게 복구
                        updated_df = updated_df[df.columns]

                        # 대량 업로드된 새 데이터의 체크박스 상태를 모두 빈 상태(False)로 초기화
                        for col in ['PO 송부', 'SC수령', 'IL 승인', '성적서', '선적서류']:
                            updated_df[col] = updated_df[col].fillna(False).astype(bool)
                        # 업로드된 수량 포맷팅 적용
                        updated_df['수량'] = updated_df['수량'].apply(lambda x: re.sub(r'(?i)([\d.,]+)\s*kg', r'\1 kg', str(x)) if pd.notna(x) else x)
                        # 선적일자도 빈칸으로 초기화 (업로드 파일에 없었을 경우 대비)
                        if '선적일자' not in updated_df.columns:
                            updated_df['선적일자'] = ""
                        updated_df['선적일자'] = updated_df['선적일자'].fillna("").astype(str)
                        if '비고' not in updated_df.columns:
                            updated_df['비고'] = ""
                        updated_df['비고'] = updated_df['비고'].fillna("").astype(str)
                        if 'PO 파일' not in updated_df.columns:
                            updated_df['PO 파일'] = ""
                        updated_df['PO 파일'] = updated_df['PO 파일'].fillna("").astype(str)
                        updated_df.to_csv(CSV_FILE, index=False)
                        st.success(f"{len(upload_data)}건의 데이터가 성공적으로 처리(추가 및 업데이트)되었습니다!")
                else:
                    st.error(f"오류: 엑셀 파일의 필수 열이 누락되었습니다. (필요한 열: {', '.join(base_cols)})")
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    with tab4:
        st.subheader("기존 구매 내역 수정")
        
        if not df.empty:
            selected_edit = st.selectbox("수정할 PO 번호를 선택하세요", df['PO 번호'].unique())
            
            # 선택된 PO 번호의 기존 데이터 가져오기
            current_data = df[df['PO 번호'] == selected_edit].iloc[0]
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                
                # 기존 수량 데이터 분리
                orig_qty = str(current_data['수량'])
                qty_num = re.sub(r'[^\d.,]', '', orig_qty)
                qty_u = re.sub(r'[\d.,\s]', '', orig_qty).upper()
                if qty_u == 'KG': qty_u = 'kg'
                if not qty_u: qty_u = "kg"
                qty_units = ["kg", "G", "L", "ML", "EA"]
                if qty_u not in qty_units: qty_units.append(qty_u)

                # 기존 가격 데이터 분리
                orig_price = str(current_data['가격'])
                price_num = re.sub(r'[^\d.,]', '', orig_price)
                price_u = re.sub(r'[\d.,\s]', '', orig_price).upper()
                if not price_u: price_u = "USD"
                price_units = ["USD", "KRW", "EUR", "JPY"]
                if price_u not in price_units: price_units.append(price_u)

                with col1:
                    new_po = st.text_input("PO 번호", value=current_data['PO 번호'])
                    new_name = st.text_input("원료명", value=current_data['원료명'])
                    
                    q_col1, q_col2 = st.columns([2, 1])
                    with q_col1:
                        new_qty_val = st.text_input("수량 (숫자)", value=qty_num)
                    with q_col2:
                        new_qty_unit = st.selectbox("수량 단위", qty_units, index=qty_units.index(qty_u), key="edit_q_unit")
                with col2:
                    p_col1, p_col2 = st.columns([1, 2])
                    with p_col1:
                        new_price_unit = st.selectbox("통화 단위", price_units, index=price_units.index(price_u), key="edit_p_unit")
                    with p_col2:
                        new_price_val = st.text_input("가격 (숫자)", value=price_num)

                    new_maker = st.text_input("제조원", value=current_data['제조원'])
                    new_supplier = st.text_input("공급원", value=current_data['공급원'])
                
                new_memo = st.text_input("비고 (메모)", value=str(current_data['비고']))
                
                if st.form_submit_button("수정 내용 저장하기"):
                    final_qty = f"{new_qty_val} {new_qty_unit}" if new_qty_val else ""
                    final_price = f"{new_price_unit} {new_price_val}" if new_price_val else ""
                    # 기존 데이터를 새로운 입력값으로 덮어쓰기
                    df.loc[df['PO 번호'] == selected_edit, ['PO 번호', '원료명', '수량', '가격', '제조원', '공급원', '비고']] = [new_po, new_name, final_qty, final_price, new_maker, new_supplier, new_memo]
                    df.to_csv(CSV_FILE, index=False)
                    st.success("수정되었습니다!")
                    st.rerun()
        else:
            st.info("수정할 데이터가 없습니다.")

    with tab6:
        st.subheader("📊 데이터 시각화 대시보드")
        
        if not df.empty:
            # 그래프를 그리기 위해 숫자로 변환한 열을 추가한 임시 데이터 생성
            df_chart = df.copy()
            df_chart['수량(숫자)'] = df_chart['수량'].apply(clean_to_number)
            df_chart['가격(숫자)'] = df_chart['가격'].apply(clean_to_number)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 📦 원료별 총 수량")
                # 원료명 기준으로 그룹화하여 수량을 합산 후 막대그래프 출력
                qty_by_material = df_chart.groupby('원료명')['수량(숫자)'].sum()
                st.bar_chart(qty_by_material)
                
            with col2:
                st.markdown("##### 💰 공급원별 총 거래 금액")
                # 공급원 기준으로 그룹화하여 가격을 합산 후 막대그래프 출력
                price_by_supplier = df_chart.groupby('공급원')['가격(숫자)'].sum()
                st.bar_chart(price_by_supplier)
        else:
            st.info("표시할 데이터가 없습니다.")

if __name__ == "__main__":
    main()
    
    