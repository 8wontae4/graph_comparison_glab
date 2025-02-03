import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Streamlit 앱 제목
st.title("CSV 데이터 비교 분석v1-Glab")

# 여러 개의 파일 업로드 지원
uploaded_files = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"], accept_multiple_files=True)

# 업로드된 파일 저장
dfs = {}
if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_csv(uploaded_file)
            dfs[uploaded_file.name] = df  # 파일 이름을 키로 데이터 저장
        except Exception as e:
            st.error(f"❌ 파일 `{uploaded_file.name}`을(를) 읽는 중 오류 발생: {e}")

# 📌 비교 분석 기능
if len(dfs) > 1:
    st.header("📊 파일 비교 분석")

    # 비교할 파일 선택 (2개 이상)
    selected_files = st.multiselect("비교할 파일을 선택하세요", list(dfs.keys()), default=list(dfs.keys())[:2])

    if len(selected_files) >= 2:
        # 공통된 숫자형 컬럼 찾기
        numeric_columns = set(dfs[selected_files[0]].select_dtypes(include=["number"]).columns)
        for file in selected_files[1:]:
            numeric_columns.intersection_update(dfs[file].select_dtypes(include=["number"]).columns)

        if numeric_columns:
            numeric_columns = sorted(list(numeric_columns))  # 정렬하여 보여주기
            st.success(f"📌 비교 가능한 숫자형 컬럼: {', '.join(numeric_columns)}")

            # X축과 Y축 선택
            x_axis = st.selectbox("📌 비교할 X축을 선택하세요", numeric_columns, key="compare_x")
            y_axis_default = "Sloat4" if "Sloat4" in numeric_columns else numeric_columns[0]
            y_axis = st.selectbox("📌 비교할 Y축을 선택하세요", numeric_columns, index=numeric_columns.index(y_axis_default), key="compare_y")

            # X축 범위 설정 (사용자 입력)
            x_min = st.number_input("📌 X축 최소값 입력", value=float(dfs[selected_files[0]][x_axis].min()))
            x_max = st.number_input("📌 X축 최대값 입력", value=float(dfs[selected_files[0]][x_axis].max()))

            # 📉 비교 그래프 생성
            st.subheader(f"📊 {x_axis} vs {y_axis} 비교 그래프")
            fig, ax = plt.subplots()

            # 비교 데이터 저장용 데이터프레임 생성
            filtered_data = {}

            # 각 파일의 데이터를 같은 그래프에 출력
            for file in selected_files:
                df_filtered = dfs[file][(dfs[file][x_axis] >= x_min) & (dfs[file][x_axis] <= x_max)]
                sns.lineplot(data=df_filtered, x=x_axis, y=y_axis, label=file, ax=ax)
                filtered_data[file] = df_filtered[[x_axis, y_axis]].copy()

            ax.set_xlim(x_min, x_max)  # X축 범위 적용
            ax.set_xlabel(x_axis)
            ax.set_ylabel(y_axis)
            ax.legend(loc='upper right', bbox_to_anchor=(1.5, 1))  # 범례를 그래프 밖 우측 상단으로 이동
            st.pyplot(fig)

            # 고유한 X축 값 정리
            all_x_values = sorted(set().union(*[df[x_axis].tolist() for df in filtered_data.values()]))
            result_df = pd.DataFrame({x_axis: all_x_values})

            # 각 파일의 Y축 값을 해당 X축 기준으로 여러 열로 추가
            for file, df in filtered_data.items():
                df_grouped = df.groupby(x_axis)[y_axis].apply(lambda x: list(x)).reset_index()
                max_repeats = df_grouped[y_axis].apply(len).max()
                y_cols = [f"{file}_Y{i+1}" for i in range(max_repeats)]
                df_expanded = df_grouped[y_axis].apply(pd.Series).rename(columns=dict(enumerate(y_cols)))
                df_final = pd.concat([df_grouped[x_axis], df_expanded], axis=1)
                result_df = result_df.merge(df_final, on=x_axis, how='left')

            # 기본 파일 이름 생성
            default_filename = selected_files[0][:12] if selected_files else "comparison"
            file_name = st.text_input("📌 다운로드할 파일명을 입력하세요", value=f"{default_filename}_result.xlsx")

            # 엑셀 파일로 변환 후 다운로드 버튼 추가
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                result_df.to_excel(writer, sheet_name='Comparison', index=False)
            output.seek(0)
            st.download_button(label="📥 비교 결과 다운로드 (Excel)", data=output, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.error("❌ 선택한 파일들 간 공통된 숫자형 컬럼이 없습니다.")
