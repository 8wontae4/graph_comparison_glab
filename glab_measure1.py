import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

def assign_pattern(df):
    pattern_num = 0
    pattern_list = []
    
    for sec in df['Sec']:
        if sec == 0:
            pattern_num += 1  # 새로운 패턴 시작 시 증가
        pattern_list.append(pattern_num)
    
    df['Pattern'] = pattern_list  # 새로운 컬럼 추가
    return df

st.title("CSV 패턴 분석 도구")

uploaded_files = st.file_uploader("CSV 다중 파일 업로드-Glab.v1", type=["csv"], accept_multiple_files=True)
file_data = {}
user_settings = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        df = pd.read_csv(uploaded_file)
        df = assign_pattern(df)  # 패턴 번호 부여
        file_name = uploaded_file.name  # 파일 이름 저장
        file_data[file_name] = df
        
        st.write(f"### 변환된 데이터 ({file_name}) (미리보기 300행)")
        st.dataframe(df.head(300))
        
        # X값 선택 기능
        x_column = st.selectbox(f"출력할 X값 선택 ({file_name})", options=df.columns, index=df.columns.get_loc("Sec") if "Sec" in df.columns else 0)
        
        # Y값 선택 기능
        y_column = st.selectbox(f"출력할 Y값 선택 ({file_name})", options=df.columns, index=df.columns.get_loc("Sloat4") if "Sloat4" in df.columns else 0)
        
        # X축 범위 설정
        min_x = st.number_input(f"X축 최소값 ({file_name})", value=df[x_column].min())
        max_x = st.number_input(f"X축 최대값 ({file_name})", value=df[x_column].max())
        
        # 패턴 선택 기능
        selected_patterns = st.multiselect(f"패턴 선택 ({file_name})", df['Pattern'].unique(), default=df['Pattern'].unique())
        filtered_df = df[df['Pattern'].isin(selected_patterns)].copy()
        filtered_df = filtered_df[(filtered_df[x_column] >= min_x) & (filtered_df[x_column] <= max_x)]
        
        # 패턴별 그래프 유형 선택 기능
        graph_types = {pattern: st.selectbox(f"패턴 {pattern} 그래프 유형 ({file_name})", ["라인", "대쉬", "산점도", "대쉬-닷"], index=0) for pattern in selected_patterns}
        line_styles = {"라인": '-', "대쉬": '--', "산점도": '', "대쉬-닷": '-.'}
        
        # 개별 파일별 그래프 출력
        st.write(f"### 패턴별 그래프 ({file_name})")
        fig, ax = plt.subplots()
        palette = sns.color_palette("hsv", len(selected_patterns))
        
        for idx, pattern in enumerate(selected_patterns):
            pattern_data = filtered_df[filtered_df['Pattern'] == pattern]
            if not pattern_data.empty:
                style = line_styles[graph_types[pattern]]
                if graph_types[pattern] == "산점도":
                    ax.scatter(pattern_data[x_column], pattern_data[y_column], label=f'P {pattern}', color=palette[idx])
                else:
                    ax.plot(pattern_data[x_column], pattern_data[y_column], linestyle=style, label=f'P {pattern}', color=palette[idx])
        
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        ax.legend()
        st.pyplot(fig)
        
        # Del ADC 그래프 출력
        st.write(f"### Del ADC 그래프 ({file_name})")
        fig2, ax2 = plt.subplots()
        
        for idx, pattern in enumerate(selected_patterns):
            pattern_data = filtered_df[filtered_df['Pattern'] == pattern].copy()
            if not pattern_data.empty:
                first_y_value = pattern_data[y_column].iloc[0]
                pattern_data['Del_ADC'] = abs(pattern_data[y_column] - first_y_value)
                style = line_styles[graph_types[pattern]]
                if graph_types[pattern] == "산점도":
                    ax2.scatter(pattern_data[x_column], pattern_data['Del_ADC'], label=f'Del ADC P {pattern}', color=palette[idx])
                else:
                    ax2.plot(pattern_data[x_column], pattern_data['Del_ADC'], linestyle=style, label=f'Del ADC P {pattern}', color=palette[idx])
        
        ax2.set_xlabel(x_column)
        ax2.set_ylabel("Del ADC")
        ax2.legend()
        st.pyplot(fig2)
        
        # 사용자 설정 저장
        user_settings[file_name] = {
            "x_column": x_column,
            "y_column": y_column,
            "min_x": min_x,
            "max_x": max_x,
            "selected_patterns": selected_patterns,
            "graph_types": graph_types
        }
    
    # 파일별 비교 그래프 복구
    st.write("### 파일별 비교 그래프")
    fig3, ax3 = plt.subplots()
    file_palette = sns.color_palette("tab10", len(file_data))
    file_color_map = {file_name: file_palette[idx] for idx, file_name in enumerate(file_data.keys())}
    
    # 파일별 비교 그래프 데이터를 저장할 리스트
    comparison_data = []
    
    for file_name, df in file_data.items():
        settings = user_settings[file_name]
        df = df[[settings["x_column"], settings["y_column"], "Pattern"]].copy()
        df["Del_ADC"] = abs(df[settings["y_column"]] - df.groupby("Pattern")[settings["y_column"]].transform("first"))
        settings = user_settings[file_name]
        x_col, y_col = settings["x_column"], settings["y_column"]
        min_x, max_x = settings["min_x"], settings["max_x"]
        selected_patterns = settings["selected_patterns"]
        graph_types = settings["graph_types"]
        
        filtered_df = df[df["Pattern"].isin(selected_patterns)].copy()
        filtered_df = filtered_df[(filtered_df[x_col] >= min_x) & (filtered_df[x_col] <= max_x)]
        
        for pattern in selected_patterns:
            pattern_data = filtered_df[filtered_df['Pattern'] == pattern].copy()
            if not pattern_data.empty:
                first_y_value = pattern_data[y_col].iloc[0]
                pattern_data['Del_ADC'] = abs(pattern_data[y_col] - first_y_value)
                style = line_styles[graph_types[pattern]]
                color = file_color_map[file_name]
                if graph_types[pattern] == "산점도":
                    ax3.scatter(pattern_data[x_col], pattern_data['Del_ADC'], label=f'{file_name.replace(".csv", "")} P {pattern}', color=color)
                else:
                    ax3.plot(pattern_data[x_col], pattern_data['Del_ADC'], linestyle=style, label=f'{file_name.replace(".csv", "")} P {pattern}', color=color)
                
                # 파일별 비교 그래프 데이터를 리스트에 추가
                comparison_data.append(pattern_data.assign(File=file_name.replace(".csv", ""), Pattern=pattern))
    
    ax3.set_xlabel("Sec")
    ax3.set_ylabel("Del ADC")
    ax3.legend(loc='upper center', bbox_to_anchor=(1.20, 1.0), ncol=1)
    st.pyplot(fig3)
    
    # 파일별 비교 그래프 데이터를 하나의 DataFrame으로 병합
    comparison_df = pd.concat(comparison_data)
    
    # "Sec" 값을 기준으로 중복 제거 및 Y축 값 열 추가
    unique_sec = comparison_df[x_col].unique()  # 고유한 "Sec" 값 추출
    result_df = pd.DataFrame({x_col: unique_sec})  # "Sec" 열 생성
    
    # 각 파일과 패턴에 대한 "Del ADC" 값을 열로 추가
    for file_name, df in file_data.items():
        settings = user_settings[file_name]
        selected_patterns = settings["selected_patterns"]
        
        for pattern in selected_patterns:
            pattern_data = comparison_df[(comparison_df["File"] == file_name.replace(".csv", "")) & (comparison_df["Pattern"] == pattern)]
            if not pattern_data.empty:
                # 파일명과 패턴 번호를 열 이름으로 사용
                col_name = f"{file_name.replace('.csv', '')}_P{pattern}_Del_ADC"
                # "Sec" 값을 기준으로 "Del ADC" 값을 매핑
                result_df = result_df.merge(pattern_data[[x_col, "Del_ADC"]].rename(columns={"Del_ADC": col_name}), on=x_col, how="left")
    
    # 다운로드 버튼 추가
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        result_df.to_excel(writer, sheet_name="Comparison_Data", index=False)
        
    output.seek(0)
    st.download_button("📥 파일별 비교 그래프 데이터 엑셀 다운로드", data=output, file_name=st.text_input("저장할 엑셀 파일 이름", value="Comparison_Data.xlsx"), mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
