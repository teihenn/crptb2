# crptb2

Crypto Trading Bot.

実際に使用しているストラテジーはcrptb2-strategyリポジトリ(private)に格納。

保守性よりとりあえずスピード重視で実装中...

## command

- Botを起動する

```bash
uv run python -m src.main
```

- Botを常時稼働にしておく

```bash
nohup uv run python -m src.main &
```

- すべてのunittestを実行する

```bash
uv run python -m unittest discover -v test
```

- 特定のunittestを実行する(例: TestIndicators)

```bash
uv run python -m unittest -v test.unit.test_indicators.TestIndicators
```

## 参考資料

### ByBit

- [取引データ](https://www.bybit.com/ja-JP/announcement-info/transact-parameters/)
  - 各シンボルの最小注文単位など
- [USDT無期限契約 - 損益の種類と計算方法](https://www.bybit.com/ja-JP/help-center/article/Profit-Loss-calculations-USDT-Contract)
- [取引手数料率](https://www.bybit.com/ja-JP/help-center/article/Trading-Fee-Structure)
