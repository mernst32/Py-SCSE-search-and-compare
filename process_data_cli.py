import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

raw_csv = 'data/moss_report.csv'
repository_names = ['Github', 'Bitbucket', 'Google_Code', 'GitLab', 'Google_Android', 'Gitorious', 'Fedora_Project']


def group_data_by_repo(df):
    # get stats about different repos and group them together
    repo_count = pd.DataFrame(data=df['Src_Repo'].value_counts()).rename(columns={'Src_Repo': 'Found_SO_Links'})
    repo_sum = pd.DataFrame(data=repo_count.sum(), columns=['Found_SO_Links'])
    repo_file_count = (df.groupby('SC_Filepath').agg({'SC_Filepath': 'count', 'Src_Repo': 'first'})) \
        .groupby('Src_Repo') \
        .agg({'Src_Repo': 'count'}).rename(columns={'Src_Repo': 'Processed_Files'})
    repo_file_sum = pd.DataFrame(data=[repo_file_count['Processed_Files'].sum()],
                                 columns=['Processed_Files'], index=['Total'])
    repo_file_count = repo_file_count.append(repo_file_sum)
    repo_df = repo_count.append(repo_sum)
    repo_df = repo_df.rename(index={'Found_SO_Links': 'Total'})
    repo_df = repo_df.join(repo_file_count)
    return repo_df


def group_data_by_filenames(df):
    # get stats grouped by Filenames
    file_data = df.groupby('SC_Filepath') \
        .agg({'Lines_Matched': 'sum', 'Code_Similarity': 'mean', 'Src_Repo': 'first'}) \
        .join(df['SC_Filepath'].value_counts()) \
        .rename(columns={'SC_Filepath': 'Found_SO_Links', 'Src_Repo': 'Repository'})
    return file_data


def get_matches_df(df):
    file_data = group_data_by_filenames(df)

    # get matching stats for repos
    matches = file_data.loc[file_data['Lines_Matched'] > 0]
    no_matches = file_data.loc[file_data['Lines_Matched'] == 0]
    count_matches = matches.groupby('Repository') \
        .agg({'Lines_Matched': 'sum', 'Code_Similarity': 'mean', 'Found_SO_Links': 'sum'}) \
        .rename(columns={'Found_SO_Links': 'Matching_SO_Links'})
    count_nomatches = no_matches.groupby('Repository') \
        .agg({'Found_SO_Links': 'sum'}) \
        .rename(columns={'Found_SO_Links': 'Not_Matching_SO_Links'})
    final_matches = count_nomatches.join(count_matches).fillna(0.0)
    matches_total = pd.DataFrame(data=[final_matches.sum()], index=['Total'])
    matches_total['Code_Similarity'] = matches_total['Code_Similarity'] / len(final_matches['Code_Similarity'])
    return final_matches.append(matches_total)


def get_percentile_copy_matches(df, copy_threshold):
    file_data = group_data_by_filenames(df)

    # get stats for the files that copied more than the copy_threshold from StackOverflow and the ones who did not
    df_copied = file_data.loc[file_data['Code_Similarity'] > copy_threshold]
    df_not_copied = file_data.loc[file_data['Code_Similarity'] <= copy_threshold]
    df_repo_copied = df_copied.groupby('Repository') \
        .agg({'Repository': 'count'}) \
        .rename(columns={'Repository': 'Copied_from_SO'})
    df_repo_not_copied = df_not_copied.groupby('Repository') \
        .agg({'Repository': 'count'}) \
        .rename(columns={'Repository': 'Not_Copied_from_SO'})
    repo_copied_total = pd.DataFrame(data=[df_repo_copied.sum()], index=['Total'])
    repo_not_copied_total = pd.DataFrame(data=[df_repo_not_copied.sum()], index=['Total'])
    df_repo_copied = df_repo_copied.append(repo_copied_total)
    df_repo_not_copied = df_repo_not_copied.append(repo_not_copied_total)
    return df_repo_not_copied.join(df_repo_copied).fillna(0.0)


def plot_overview(df):
    setup_plot_repository(df, 'Total')
    # function to show the plot
    print("Plot the overview as a box-plot...")
    plt.show()


def setup_plot_repository(df, repo_name):
    print('Setup plot of the ', repo_name, 'data...')

    left = [1, 2, 3, 4]
    repo_df = df.loc[repo_name, :]
    height = [repo_df.loc['Processed_Files'], repo_df.loc['Found_SO_Links'], repo_df.loc['Copied_from_SO'],
              repo_df.loc['Not_Copied_from_SO']]
    tick_label = ['gef. Dateien', 'gef. SO Links', 'Kopiert', 'Nicht Kopiert']
    plt.grid(linestyle='dashed')
    plt.bar(left, height, tick_label=tick_label, width=0.4, color=['white'], edgecolor=['black'])
    plt.title(repo_name)


def calc_copy_percent(df, index):
    repo_df = df.loc[index, :]

    total = repo_df.loc['Processed_Files']
    copied = repo_df.loc['Copied_from_SO']
    not_copied = repo_df.loc['Not_Copied_from_SO']

    copied_percent = (copied / total) * 100
    not_copied_percent = (not_copied / total) * 100

    return copied_percent, not_copied_percent


def calc_percent(df, index):
    total = df.loc['Total', 'Processed_Files']
    repo = df.loc[index, 'Processed_Files']

    percentage = (repo / total) * 100

    return percentage


def do_plotting_with_threshold(df, copy_threshold, percent=True):
    if percent:
        a_list = repository_names.copy()
        a_list.append('Total')
        copied_list = []
        not_copied_list = []
        for repository_name in a_list:
            repo_copied_percent, repo_not_copied_percent = calc_copy_percent(df, repository_name)

            copied_list.append(repo_copied_percent)
            not_copied_list.append(repo_not_copied_percent)
        n = len(a_list)
        ind = np.arange(n)
        width = 0.4

        p1 = plt.bar(ind, not_copied_list, width, color=['green'], edgecolor=['black'])
        p2 = plt.bar(ind, copied_list, width, bottom=not_copied_list, color=['red'], edgecolor=['black'])

        plt.ylabel('Prozent')
        plt.title('Wieviel wurde von SO kopiert? (copy_threshold = {}, Prozent)'.format(copy_threshold))
        plt.xticks(ind, a_list)
        plt.yticks(np.arange(0, 120, 10))
        plt.legend((p1[0], p2[0]), ('Nicht kopiert', 'Kopiert'))
        print('Plotting box-plot for the comparison of copied and not copied files with relative data and the copy_'
              'threshold', str(copy_threshold), '...')
        plt.show()
    else:
        a_list = repository_names.copy()
        a_list.append('Total')
        copied_list = []
        not_copied_list = []
        for repository_name in a_list:
            repo_copied_percent = df.loc[repository_name, 'Copied_from_SO']
            repo_not_copied_percent = df.loc[repository_name, 'Not_Copied_from_SO']

            copied_list.append(repo_copied_percent)
            not_copied_list.append(repo_not_copied_percent)
        n = len(a_list)
        ind = np.arange(n)
        width = 0.4

        p1 = plt.bar(ind, not_copied_list, width, color=['green'], edgecolor=['black'])
        p2 = plt.bar(ind, copied_list, width, bottom=not_copied_list, color=['red'], edgecolor=['black'])

        plt.ylabel('Analysierte Dateien')
        plt.title('Wieviel wurde von SO kopiert? (copy_threshold = {}, Absolut)'.format(copy_threshold))
        plt.xticks(ind, a_list)
        plt.yticks(np.arange(0, df.loc['Total', 'Processed_Files'] + 200, 100))
        plt.legend((p1[0], p2[0]), ('Nicht kopiert', 'Kopiert'))
        print('Plotting box-plot for the comparison of copied and not copied files with absolute data and the '
              'copy_threshold', str(copy_threshold), '...')
        plt.show()


def plot_pie_chart(df):
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    sizes = []
    others = []
    others_labels = []
    for name in repository_names:
        percent = calc_percent(df, name)
        if percent > 10:
            sizes.append(percent)
        else:
            others.append(percent)
            others_labels.append(name)
    if len(others) != 0:
        others_size = 0
        for other in others:
            others_size = others_size + other
        sizes.append(others_size)
        labels = repository_names.copy()
        for rem in others_labels:
            labels.remove(rem)
        labels.append('Andere')
        explode = np.zeros(len(sizes))
    else:
        labels = repository_names
        explode = np.zeros(len(sizes))

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    print('Plotting the division of files as a pie-chart...')
    plt.show()


def plot_copy_threshold_comparison(df_list, percent=True):
    if not percent:
        copied_list = []
        not_copied_list = []
        for df_final in df_list:
            copied = df_final.loc['Total', 'Copied_from_SO']
            not_copied = df_final.loc['Total', 'Not_Copied_from_SO']

            copied_list.append(copied)
            not_copied_list.append(not_copied)
        n = len(df_list)
        ind = np.arange(n)
        width = 0.4

        p1 = plt.bar(ind, not_copied_list, width, color=['green'], edgecolor=['black'])
        p2 = plt.bar(ind, copied_list, width, bottom=not_copied_list, color=['red'], edgecolor=['black'])

        plt.ylabel('Anzahl der analysierten Dateien')
        plt.xlabel('Die Übereinstimmungsschwellwerte')
        plt.title('Gegenüberstellung der Ergebnisse für die unterschiedlichen Schwellwerte (Absolut)')
        plt.xticks(ind, ['1 %', '25 %', '50 %', '75 %'])
        plt.yticks(np.arange(0, df_list[0].loc['Total', 'Processed_Files'] + 200, 100))
        plt.legend((p1[0], p2[0]), ('Nicht kopiert', 'Kopiert'))
        print('Plotting box-plot for the comparison of copied and not copied files as absolute...')
        plt.show()
    else:
        copied_list = []
        not_copied_list = []
        for df_final in df_list:
            copied_percent, not_copied_percent = calc_copy_percent(df_final, 'Total')
            copied_list.append(copied_percent)
            not_copied_list.append(not_copied_percent)
        n = len(df_list)
        ind = np.arange(n)
        width = 0.4

        p1 = plt.bar(ind, not_copied_list, width, color=['green'], edgecolor=['black'])
        p2 = plt.bar(ind, copied_list, width, bottom=not_copied_list, color=['red'], edgecolor=['black'])

        plt.ylabel('Prozent')
        plt.xlabel('Die Übereinstimmungsschwellwerte')
        plt.title('Gegenüberstellung der Ergebnisse für die unterschiedlichen Schwellwerte (Prozent)')
        plt.xticks(ind, ['1 %', '25 %', '50 %', '75 %'])
        plt.yticks(np.arange(0, 120, 10))
        plt.legend((p1[0], p2[0]), ('Nicht kopiert', 'Kopiert'))
        print('Plotting box-plot for the comparison of copied and not copied files as percent...')
        plt.show()


if __name__ == "__main__":
    print('Parsing data from CSV file:', raw_csv + '...')
    data_frame = pd.read_csv(raw_csv, usecols=['SC_Filepath', 'Stackoverflow_Links', 'File_1', 'File_2',
                                               'Lines_Matched', 'Code_Similarity', 'Src_Repo'])

    df_matches = get_matches_df(data_frame)
    df_repo = group_data_by_repo(data_frame)

    # join repo stats and matching stats for repos together
    df_repo_stats = df_matches.join(df_repo)

    plot_pie_chart(df_repo_stats)

    # get stats for the files that had more than half of a match with StackOverflow snippets and the ones who did not
    df_copied_list = []

    df_copied_stats_with_001 = get_percentile_copy_matches(data_frame, 0.01)
    df_final_001 = df_repo_stats.join(df_copied_stats_with_001).sort_values(by=['Found_SO_Links'])
    df_copied_list.append(df_final_001)

    df_copied_stats_with_025 = get_percentile_copy_matches(data_frame, 0.25)
    df_final_025 = df_repo_stats.join(df_copied_stats_with_025).sort_values(by=['Found_SO_Links'])
    df_copied_list.append(df_final_025)

    df_copied_stats_with_050 = get_percentile_copy_matches(data_frame, 0.50)
    df_final_050 = df_repo_stats.join(df_copied_stats_with_050).sort_values(by=['Found_SO_Links'])
    df_copied_list.append(df_final_050)

    df_copied_stats_with_075 = get_percentile_copy_matches(data_frame, 0.75)
    df_final_075 = df_repo_stats.join(df_copied_stats_with_075).sort_values(by=['Found_SO_Links'])
    df_copied_list.append(df_final_075)

    plot_copy_threshold_comparison(df_copied_list, percent=True)
    plot_copy_threshold_comparison(df_copied_list, percent=False)

    do_plotting_with_threshold(df_final_025, 0.25, percent=True)
    do_plotting_with_threshold(df_final_025, 0.25, percent=False)

    print('\n', df_final_025)

    print('\nDone')
