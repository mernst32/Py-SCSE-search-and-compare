import statistics
import pandas as pd
import numpy as np

raw_csv = 'data/moss_report.csv'

if __name__ == "__main__":
    df = pd.read_csv(raw_csv, usecols=['SC_Filepath', 'Stackoverflow_Links', 'File_1', 'File_2', 'Lines_Matched',
                                       'Code_Similarity', 'Src_Repo'])

    # get stats about different repos and group them together
    repo_count = pd.DataFrame(data=df['Src_Repo'].value_counts()).rename(columns={'Src_Repo': 'Found_SO_Links'})
    repo_sum = pd.DataFrame(data=repo_count.sum(), columns=['Found_SO_Links'])
    repo_file_count = (df.groupby('SC_Filepath').agg({'SC_Filepath': 'count', 'Src_Repo': 'first'}))\
        .groupby('Src_Repo')\
        .agg({'Src_Repo': 'count'}).rename(columns={'Src_Repo': 'Processed_Files'})
    repo_file_sum = pd.DataFrame(data=[repo_file_count['Processed_Files'].sum()],
                                 columns=['Processed_Files'], index=['Total'])
    repo_file_count = repo_file_count.append(repo_file_sum)
    repo_df = repo_count.append(repo_sum)
    repo_df = repo_df.rename(index={'Found_SO_Links': 'Total'})
    repo_df = repo_df.join(repo_file_count)

    # get stats grouped by Filenames
    file_data = df.groupby('SC_Filepath')\
        .agg({'Lines_Matched': 'sum', 'Code_Similarity': 'mean', 'Src_Repo': 'first'})\
        .join(df['SC_Filepath'].value_counts())\
        .rename(columns={'SC_Filepath': 'Found_SO_Links', 'Src_Repo': 'Repository'})

    # get matching stats for repos
    df_matches = file_data.loc[file_data['Lines_Matched'] > 0]
    df_no_matches = file_data.loc[file_data['Lines_Matched'] == 0]
    count_matches = df_matches.groupby('Repository')\
        .agg({'Lines_Matched': 'sum', 'Code_Similarity': 'mean', 'Found_SO_Links': 'sum'})\
        .rename(columns={'Found_SO_Links': 'Matching_SO_Links'})
    count_nomatches = df_no_matches.groupby('Repository') \
        .agg({'Found_SO_Links': 'sum'})\
        .rename(columns={'Found_SO_Links': 'Not_Matching_SO_Links'})
    matches = count_nomatches.join(count_matches).fillna(0.0)
    matches_total = pd.DataFrame(data=[matches.sum()], index=['Total'])
    matches_total['Code_Similarity'] = matches_total['Code_Similarity']/len(matches['Code_Similarity'])
    matches = matches.append(matches_total)

    # join repo stats and matching stats for repos together
    df_repo_stats = matches.join(repo_df)

    # get stats for the files that copied more than half from StackOverflow and the ones who did not
    df_copied = file_data.loc[file_data['Code_Similarity'] > 0.5]
    df_not_copied = file_data.loc[file_data['Code_Similarity'] <= 0.5]
    df_repo_copied = df_copied.groupby('Repository')\
        .agg({'Repository': 'count'})\
        .rename(columns={'Repository': 'Copied_from_SO'})
    df_repo_not_copied = df_not_copied.groupby('Repository')\
        .agg({'Repository': 'count'})\
        .rename(columns={'Repository': 'Not_Copied_from_SO'})
    repo_copied_total = pd.DataFrame(data=[df_repo_copied.sum()], index=['Total'])
    repo_not_copied_total = pd.DataFrame(data=[df_repo_not_copied.sum()], index=['Total'])
    df_repo_copied = df_repo_copied.append(repo_copied_total)
    df_repo_not_copied = df_repo_not_copied.append(repo_not_copied_total)
    df_copied_stats = df_repo_not_copied.join(df_repo_copied).fillna(0.0)

    # put everything together
    df_final = df_repo_stats.join(df_copied_stats).sort_values(by=['Found_SO_Links'])
    print('The gathered data as a', type(df_final).__name__, ':')
    print(df_final)
