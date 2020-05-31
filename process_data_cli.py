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


if __name__ == "__main__":
    print('Parsing data from CSV file:', raw_csv + '...')
    data_frame = pd.read_csv(raw_csv, usecols=['SC_Filepath', 'Stackoverflow_Links', 'File_1', 'File_2',
                                               'Lines_Matched', 'Code_Similarity', 'Src_Repo'])

    df_matches = get_matches_df(data_frame)
    df_repo = group_data_by_repo(data_frame)

    # join repo stats and matching stats for repos together
    df_repo_stats = df_matches.join(df_repo)

    # get stats for the files that had more than half of a match with StackOverflow snippets and the ones who did not
    df_copied_stats = get_percentile_copy_matches(data_frame, 0.5)

    # put everything together
    df_final = df_repo_stats.join(df_copied_stats).sort_values(by=['Found_SO_Links'])
    print('\nThe parsed data as a', type(df_final).__name__, ':')
    print(df_final, '\n')

    plot_overview(df_final)

    fig = plt.figure()
    n_cols = 3
    n_rows = (len(repository_names) / n_cols) + 1
    for count, repository_name in enumerate(repository_names):
        plt.subplot(n_rows, n_cols, count + 1)
        setup_plot_repository(df_final, repository_name)
    # adjusting space between subplots
    fig.subplots_adjust(hspace=.5, wspace=.1)
    print('Plotting grid arrangement of all Repos...')
    # function to show the plot
    plt.show()

    a_list = repository_names.copy()
    a_list.append('Total')
    copied_list = []
    not_copied_list = []
    for repository_name in a_list:
        repo_copied_percent, repo_not_copied_percent = calc_copy_percent(df_final, repository_name)
        copied_list.append(repo_copied_percent)
        not_copied_list.append(repo_not_copied_percent)
    N = len(a_list)
    ind = np.arange(N)
    width = 0.4

    p1 = plt.bar(ind, not_copied_list, width, color=['green'], edgecolor=['black'])
    p2 = plt.bar(ind, copied_list, width, bottom=not_copied_list, color=['red'], edgecolor=['black'])

    plt.ylabel('Prozent')
    plt.title('Wieviel wurde prozentuell von SO kopiert')
    plt.xticks(ind, a_list)
    plt.yticks(np.arange(0, 120, 10))
    plt.legend((p1[0], p2[0]), ('Nicht kopiert', 'Kopiert'))
    print('Plotting box-plot for the comparison of copied and not copied files...')
    plt.show()

    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    sizes = []
    others = []
    others_labels = []
    for repository_name in repository_names:
        percent = calc_percent(df_final, repository_name)
        if percent > 10:
            sizes.append(percent)
        else:
            others.append(percent)
            others_labels.append(repository_name)
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
    print('\nDone')


