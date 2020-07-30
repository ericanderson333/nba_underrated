import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import os

URL = 'https://stats.nba.com/leaders/'
PLAYER_AMOUNT = 120 #Enter in how many players you want here


def get_avg_stats():
    # Open data table and make sure all stats are showing, not just by page
    driver = webdriver.Chrome()
    driver.get(URL)
    class_name = driver.find_element_by_class_name('stats-table-pagination__info')
    drop_down_menu = Select(class_name.find_element_by_css_selector(
        'select[class="stats-table-pagination__select ng-pristine ng-untouched ng-valid ng-not-empty"]'))
    drop_down_menu.select_by_visible_text('All')

    # Get page src and pass it through beautifulsoup
    html = driver.page_source
    driver.close()
    soup = BeautifulSoup(html, 'html.parser')

    # get all the columns, replace all whitespace and new lines
    columns = [th.getText() for th in soup.findAll('tr')[0].findAll('th')]
    columns[1] = columns[1].replace('\n', '').replace(' ', '')

    # get all rows, replace all whitespace and new lines
    rows = soup.findAll('tr')[1:]
    avg_stats = [[td.getText().replace('\n', '').strip() for td in rows[i].findAll('td')]
                 for i in range(len(rows))]

    # create data set, drop extra data as well as the rankings
    df = pd.DataFrame(avg_stats, columns=columns)
    df.drop(index=df.index[262::], columns=['#'], inplace=True)
    if not os.path.exists('csv_files'):
        os.makedirs('csv_files')
    df = resort_by_min(df)
    if df is None:
        return
    df.to_csv('csv_files/avg_player_stats.csv')


def resort_by_min(df):
    if df.empty:
        print('Error')
        return None

    #sort by avg minutes
    df = df.sort_values(by='MIN', ascending=False)
    df.reset_index(drop=True, inplace=True)
    return df

def find_underrated():
    main_df = pd.read_csv('csv_files/avg_player_stats.csv')

    #drop unnamed column (deleting extra index column)
    main_df.drop(main_df.columns[main_df.columns.str.contains('unnamed', case=False)], axis=1, inplace=True)

    #find top 50 players by minute, calc average minutes from array
    top_50 = main_df['MIN'][0:50]
    avg = find_top_min_avg(top_50)

    #we need dataset of just bottom players, lets take bottom 60 players,
    #this would take the two worst players from each team
    bottom_index = len(main_df.index) - PLAYER_AMOUNT
    temp_df = main_df.loc[bottom_index::]

    #pass through calc function, this will return new data set
    #sort by efficiency and reindex
    bottom_df = calc_underrated(temp_df, avg)
    bottom_df = bottom_df.sort_values(by='EFF', ascending=False)
    bottom_df.reset_index(drop=True, inplace=True)
    if bottom_df is None:
        return
    bottom_df.to_csv('csv_files/underrated_players.csv')



def find_top_min_avg(top_50):

    #calculate top 50 players average minutes
    avg = 0
    for count, num in enumerate(top_50):
        avg += num
    return round((avg/count), 1)

def calc_underrated(bottom_df, top_avg):
    if bottom_df.empty:
        print('Error')
        return None

    #drop columns that can't be determined based off change, create columns we can determine change on
    columns_affected = ['MIN', 'PTS', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'EFF']
    columns_to_drop = ['FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%']

    #mult = multiplier per stat column, then drop the above columns that need to be dropped
    for i in bottom_df.index:
        mult = (top_avg/bottom_df['MIN'][i])
        for col in columns_affected:
            bottom_df[col][i] = round(bottom_df[col][i] * mult, 1)
    bottom_df.drop(columns=columns_to_drop, inplace=True)
    return bottom_df

if __name__ == '__main__':
    get_avg_stats()
    find_underrated()
    print('View CSV files!')