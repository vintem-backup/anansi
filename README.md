# Anansi

[![pipeline status](https://gitlab.com/marcusmello/anansi/badges/master/pipeline.svg)](https://gitlab.com/marcusmello/anansi/-/commits/master) [![coverage report](https://gitlab.com/marcusmello/anansi/badges/master/coverage.svg)](https://gitlab.com/marcusmello/anansi/-/commits/master)

## Dependencies

Python, if you're using anansi installed by pip; if you're developing Pip, Poetry.

To install [poetry](https://python-poetry.org/docs/#installation), on
osx, linux or *bashonwindows* terminals, type it:

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

Alternatively, poetry could be installed by pip (supposing you have
python and pip already installed):

    pip install poetry

## How to install Anansi Toolkit

Just type:

    pip install anansi-toolkit

or clone it from this repo and install it's dependencies by doing:

    git clone gitlab.com/marcusmello/anansi
    poetry install

## Consuming on Jupyter notebook

**That is only a suggestion, you could run anansi on any python
terminal. Only tested on linux.**

Install the anansi-toolkit kernel (virtual environment with all needed
dependencies):

    poetry run python -m ipykernel install --user --name=$(basename $(pwd))

... or:  

    poetry run python -m ipykernel install --user --name=(basename (pwd))

if you are a [fish](https://fishshell.com/ "command line shell interpreter")
user.

And, finally:

    poetry run jupyter notebook

or, if you want to release the prompt, do:

    poetry run jupyter notebook > jupyterlog 2>&1 &

## Consuming on python terminal

You must have to do this on a isolated environment, with dependencies embedded, doing:

    poetry shell
    python

## Straight to the point: Running Default Back Testing Operation

### Importing Dependencies

```python
from anansi_toolkit.tradingbot.models import *
from anansi_toolkit.tradingbot import traders
from anansi_toolkit.tradingbot.views import create_user, create_default_back_testing_operation
```

### Add a new user

```py
my_user_first_name = "John"

create_user(first_name=my_user_first_name,
                   last_name="Doe",
                   email = "{}@email.com".format(my_user_first_name.lower()))
```

### Creating a default back testing operation

```python
my_user = User[1]
create_default_back_testing_operation(user=my_user)
```

### Instantiating a trader

```python
my_op = Operation.get(id=1)
my_trader = traders.DefaultTrader(operation=my_op)
```

### Run the trader

```python
my_trader.run()
```

## Playing with the database models

### Getting all users

```python
users = select(user for user in User)
users.show()
```

    id|first_name|last_name|login_displayed_name|email         
    --+----------+---------+--------------------+--------------
    1 |John      |Doe      |                    |john@email.com

```python
my_user.first_name
```

    'John'

### Some operation attribute

```python
my_op.stop_loss.name
```

    'StopTrailing3T'

### Some trader attribute

```python
my_trader.Classifier.parameters.time_frame
```

    '6h'

### Updating some attributes

```python
before_update = my_trader.operation.position.side, my_trader.operation.position.exit_reference_price

my_trader.operation.position.update(side="Long", exit_reference_price=1020.94)

after_update = my_trader.operation.position.side, my_trader.operation.position.exit_reference_price

before_update, after_update
```

    (('Zeroed', None), ('Long', 1020.94))

## Requesting klines

### Klines treated and ready for use, including market indicators methods

The example below uses the 'FromBroker' class from the 'klines'
module ('marketdata' package), which works as an abstraction over the
'brokers' layer, not only queueing requests (in order to respect
brokers limits), but also conforming the klines like a pandas
dataframe,
[extended](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.api.extensions.register_dataframe_accessor.html)
with market indicator methods.

```python
from anansi_toolkit.marketdata import klines
```

```python
BinanceKlines = klines.FromBroker(
  broker_name="binance", ticker_symbol="BTCUSDT", time_frame="1h")
```

```python
newest_klines = BinanceKlines.newest(2167)
```

```python
newest_klines
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Open_time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2020-06-17 11:00:00</td>
      <td>9483.25</td>
      <td>9511.53</td>
      <td>9466.00</td>
      <td>9478.61</td>
      <td>1251.802697</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2020-06-17 12:00:00</td>
      <td>9478.61</td>
      <td>9510.88</td>
      <td>9477.35</td>
      <td>9499.25</td>
      <td>1120.426332</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2020-06-17 13:00:00</td>
      <td>9499.24</td>
      <td>9565.00</td>
      <td>9432.00</td>
      <td>9443.48</td>
      <td>4401.693008</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2020-06-17 14:00:00</td>
      <td>9442.50</td>
      <td>9464.83</td>
      <td>9366.09</td>
      <td>9410.95</td>
      <td>4802.211120</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2020-06-17 15:00:00</td>
      <td>9411.27</td>
      <td>9436.54</td>
      <td>9388.43</td>
      <td>9399.24</td>
      <td>2077.135281</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>2162</th>
      <td>2020-09-15 13:00:00</td>
      <td>10907.94</td>
      <td>10917.96</td>
      <td>10834.00</td>
      <td>10834.71</td>
      <td>3326.420940</td>
    </tr>
    <tr>
      <th>2163</th>
      <td>2020-09-15 14:00:00</td>
      <td>10834.71</td>
      <td>10879.00</td>
      <td>10736.63</td>
      <td>10764.19</td>
      <td>4382.021477</td>
    </tr>
    <tr>
      <th>2164</th>
      <td>2020-09-15 15:00:00</td>
      <td>10763.37</td>
      <td>10815.47</td>
      <td>10745.63</td>
      <td>10784.46</td>
      <td>3531.309654</td>
    </tr>
    <tr>
      <th>2165</th>
      <td>2020-09-15 16:00:00</td>
      <td>10785.23</td>
      <td>10827.61</td>
      <td>10700.00</td>
      <td>10784.23</td>
      <td>3348.735166</td>
    </tr>
    <tr>
      <th>2166</th>
      <td>2020-09-15 17:00:00</td>
      <td>10784.23</td>
      <td>10812.44</td>
      <td>10738.33</td>
      <td>10794.84</td>
      <td>1931.035921</td>
    </tr>
  </tbody>
</table>
<p>2167 rows × 6 columns</p>
</div>

### Applying simple moving average  indicators

```python
indicator = newest_klines.apply_indicator.trend.simple_moving_average(number_of_candles=35)
```

```python
indicator.name, indicator.last(), indicator.series
```

    ('sma_ohlc4_35',
     10669.49407142858,
     0                NaN
     1                NaN
     2                NaN
     3                NaN
     4                NaN
                 ...     
     2162    10619.190500
     2163    10632.213571
     2164    10644.682643
     2165    10657.128857
     2166    10669.494071
     Length: 2167, dtype: float64)

```python
newest_klines
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Open_time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2020-06-17 11:00:00</td>
      <td>9483.25</td>
      <td>9511.53</td>
      <td>9466.00</td>
      <td>9478.61</td>
      <td>1251.802697</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2020-06-17 12:00:00</td>
      <td>9478.61</td>
      <td>9510.88</td>
      <td>9477.35</td>
      <td>9499.25</td>
      <td>1120.426332</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2020-06-17 13:00:00</td>
      <td>9499.24</td>
      <td>9565.00</td>
      <td>9432.00</td>
      <td>9443.48</td>
      <td>4401.693008</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2020-06-17 14:00:00</td>
      <td>9442.50</td>
      <td>9464.83</td>
      <td>9366.09</td>
      <td>9410.95</td>
      <td>4802.211120</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2020-06-17 15:00:00</td>
      <td>9411.27</td>
      <td>9436.54</td>
      <td>9388.43</td>
      <td>9399.24</td>
      <td>2077.135281</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>2162</th>
      <td>2020-09-15 13:00:00</td>
      <td>10907.94</td>
      <td>10917.96</td>
      <td>10834.00</td>
      <td>10834.71</td>
      <td>3326.420940</td>
    </tr>
    <tr>
      <th>2163</th>
      <td>2020-09-15 14:00:00</td>
      <td>10834.71</td>
      <td>10879.00</td>
      <td>10736.63</td>
      <td>10764.19</td>
      <td>4382.021477</td>
    </tr>
    <tr>
      <th>2164</th>
      <td>2020-09-15 15:00:00</td>
      <td>10763.37</td>
      <td>10815.47</td>
      <td>10745.63</td>
      <td>10784.46</td>
      <td>3531.309654</td>
    </tr>
    <tr>
      <th>2165</th>
      <td>2020-09-15 16:00:00</td>
      <td>10785.23</td>
      <td>10827.61</td>
      <td>10700.00</td>
      <td>10784.23</td>
      <td>3348.735166</td>
    </tr>
    <tr>
      <th>2166</th>
      <td>2020-09-15 17:00:00</td>
      <td>10784.23</td>
      <td>10812.44</td>
      <td>10738.33</td>
      <td>10794.84</td>
      <td>1931.035921</td>
    </tr>
  </tbody>
</table>
<p>2167 rows × 6 columns</p>
</div>

### Same as above, but showing indicator column

```python
indicator = newest_klines.apply_indicator.trend.simple_moving_average(
  number_of_candles=35, indicator_column="SMA_OHLC4_n35")
```

```python
newest_klines
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Open_time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
      <th>SMA_OHLC4_n35</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2020-06-17 11:00:00</td>
      <td>9483.25</td>
      <td>9511.53</td>
      <td>9466.00</td>
      <td>9478.61</td>
      <td>1251.802697</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2020-06-17 12:00:00</td>
      <td>9478.61</td>
      <td>9510.88</td>
      <td>9477.35</td>
      <td>9499.25</td>
      <td>1120.426332</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2020-06-17 13:00:00</td>
      <td>9499.24</td>
      <td>9565.00</td>
      <td>9432.00</td>
      <td>9443.48</td>
      <td>4401.693008</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2020-06-17 14:00:00</td>
      <td>9442.50</td>
      <td>9464.83</td>
      <td>9366.09</td>
      <td>9410.95</td>
      <td>4802.211120</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2020-06-17 15:00:00</td>
      <td>9411.27</td>
      <td>9436.54</td>
      <td>9388.43</td>
      <td>9399.24</td>
      <td>2077.135281</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>2162</th>
      <td>2020-09-15 13:00:00</td>
      <td>10907.94</td>
      <td>10917.96</td>
      <td>10834.00</td>
      <td>10834.71</td>
      <td>3326.420940</td>
      <td>10619.190500</td>
    </tr>
    <tr>
      <th>2163</th>
      <td>2020-09-15 14:00:00</td>
      <td>10834.71</td>
      <td>10879.00</td>
      <td>10736.63</td>
      <td>10764.19</td>
      <td>4382.021477</td>
      <td>10632.213571</td>
    </tr>
    <tr>
      <th>2164</th>
      <td>2020-09-15 15:00:00</td>
      <td>10763.37</td>
      <td>10815.47</td>
      <td>10745.63</td>
      <td>10784.46</td>
      <td>3531.309654</td>
      <td>10644.682643</td>
    </tr>
    <tr>
      <th>2165</th>
      <td>2020-09-15 16:00:00</td>
      <td>10785.23</td>
      <td>10827.61</td>
      <td>10700.00</td>
      <td>10784.23</td>
      <td>3348.735166</td>
      <td>10657.128857</td>
    </tr>
    <tr>
      <th>2166</th>
      <td>2020-09-15 17:00:00</td>
      <td>10784.23</td>
      <td>10812.44</td>
      <td>10738.33</td>
      <td>10794.84</td>
      <td>1931.035921</td>
      <td>10669.494071</td>
    </tr>
  </tbody>
</table>
<p>2167 rows × 7 columns</p>
</div>

### Raw klines, using the low level abstraction module "*brokers*"

**DISCLAIMER: Requests here are not queued! There is a risk of banning
the IP or even blocking API keys if some limits are exceeded. Use with
caution.**

```python
from anansi_toolkit.share import brokers
```

```python
binance_broker = brokers.Binance()
```

```python
my_klines = binance_broker.get_klines(ticker_symbol="BTCUSDT", time_frame="1m")
```

```python
my_klines
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Open_time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1600165560</td>
      <td>10688.12</td>
      <td>10691.14</td>
      <td>10684.88</td>
      <td>10684.88</td>
      <td>21.529835</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1600165620</td>
      <td>10684.88</td>
      <td>10686.15</td>
      <td>10681.84</td>
      <td>10685.99</td>
      <td>18.487428</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1600165680</td>
      <td>10686.00</td>
      <td>10687.65</td>
      <td>10684.92</td>
      <td>10687.09</td>
      <td>22.246376</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1600165740</td>
      <td>10687.09</td>
      <td>10689.54</td>
      <td>10683.86</td>
      <td>10687.26</td>
      <td>18.818481</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1600165800</td>
      <td>10687.26</td>
      <td>10687.26</td>
      <td>10683.71</td>
      <td>10685.76</td>
      <td>38.281582</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>494</th>
      <td>1600195200</td>
      <td>10762.43</td>
      <td>10763.48</td>
      <td>10760.35</td>
      <td>10760.75</td>
      <td>8.572210</td>
    </tr>
    <tr>
      <th>495</th>
      <td>1600195260</td>
      <td>10760.75</td>
      <td>10762.48</td>
      <td>10759.30</td>
      <td>10759.31</td>
      <td>11.089815</td>
    </tr>
    <tr>
      <th>496</th>
      <td>1600195320</td>
      <td>10759.30</td>
      <td>10762.22</td>
      <td>10755.39</td>
      <td>10761.26</td>
      <td>27.070820</td>
    </tr>
    <tr>
      <th>497</th>
      <td>1600195380</td>
      <td>10761.26</td>
      <td>10761.26</td>
      <td>10751.74</td>
      <td>10756.02</td>
      <td>15.482246</td>
    </tr>
    <tr>
      <th>498</th>
      <td>1600195440</td>
      <td>10755.61</td>
      <td>10756.57</td>
      <td>10748.03</td>
      <td>10748.04</td>
      <td>61.153777</td>
    </tr>
  </tbody>
</table>
<p>499 rows × 6 columns</p>
</div>

### Same as above, but returning all information got from broker

```python
my_klines = binance_broker.get_klines(ticker_symbol="BTCUSDT", time_frame="1m", show_only_desired_info=False)
```

```python
my_klines
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Open_time</th>
      <th>Open</th>
      <th>High</th>
      <th>Low</th>
      <th>Close</th>
      <th>Volume</th>
      <th>Close_time</th>
      <th>Quote_asset_volume</th>
      <th>Number_of_trades</th>
      <th>Taker_buy_base_asset_volume</th>
      <th>Taker_buy_quote_asset_volume</th>
      <th>Ignore</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1600165560</td>
      <td>10688.12</td>
      <td>10691.14</td>
      <td>10684.88</td>
      <td>10684.88</td>
      <td>21.529835</td>
      <td>1600165619</td>
      <td>230126.587773</td>
      <td>373.0</td>
      <td>10.279415</td>
      <td>109864.149822</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1600165620</td>
      <td>10684.88</td>
      <td>10686.15</td>
      <td>10681.84</td>
      <td>10685.99</td>
      <td>18.487428</td>
      <td>1600165679</td>
      <td>197536.180849</td>
      <td>336.0</td>
      <td>8.256498</td>
      <td>88223.566054</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1600165680</td>
      <td>10686.00</td>
      <td>10687.65</td>
      <td>10684.92</td>
      <td>10687.09</td>
      <td>22.246376</td>
      <td>1600165739</td>
      <td>237738.839831</td>
      <td>415.0</td>
      <td>13.378805</td>
      <td>142975.243246</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1600165740</td>
      <td>10687.09</td>
      <td>10689.54</td>
      <td>10683.86</td>
      <td>10687.26</td>
      <td>18.818481</td>
      <td>1600165799</td>
      <td>201100.293663</td>
      <td>539.0</td>
      <td>9.062957</td>
      <td>96849.611844</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1600165800</td>
      <td>10687.26</td>
      <td>10687.26</td>
      <td>10683.71</td>
      <td>10685.76</td>
      <td>38.281582</td>
      <td>1600165859</td>
      <td>409068.511314</td>
      <td>534.0</td>
      <td>16.799813</td>
      <td>179523.708531</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>494</th>
      <td>1600195200</td>
      <td>10762.43</td>
      <td>10763.48</td>
      <td>10760.35</td>
      <td>10760.75</td>
      <td>8.572210</td>
      <td>1600195259</td>
      <td>92253.016477</td>
      <td>292.0</td>
      <td>2.394778</td>
      <td>25771.715413</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>495</th>
      <td>1600195260</td>
      <td>10760.75</td>
      <td>10762.48</td>
      <td>10759.30</td>
      <td>10759.31</td>
      <td>11.089815</td>
      <td>1600195319</td>
      <td>119341.014647</td>
      <td>277.0</td>
      <td>3.064458</td>
      <td>32976.256534</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>496</th>
      <td>1600195320</td>
      <td>10759.30</td>
      <td>10762.22</td>
      <td>10755.39</td>
      <td>10761.26</td>
      <td>27.070820</td>
      <td>1600195379</td>
      <td>291245.877535</td>
      <td>490.0</td>
      <td>14.654896</td>
      <td>157679.926758</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>497</th>
      <td>1600195380</td>
      <td>10761.26</td>
      <td>10761.26</td>
      <td>10751.74</td>
      <td>10756.02</td>
      <td>15.482246</td>
      <td>1600195439</td>
      <td>166520.446192</td>
      <td>353.0</td>
      <td>7.390407</td>
      <td>79491.160961</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>498</th>
      <td>1600195440</td>
      <td>10755.61</td>
      <td>10756.57</td>
      <td>10748.03</td>
      <td>10748.04</td>
      <td>61.153777</td>
      <td>1600195499</td>
      <td>657520.935924</td>
      <td>585.0</td>
      <td>13.436657</td>
      <td>144474.084684</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
<p>499 rows × 12 columns</p>
</div>
