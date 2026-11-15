# Equations

Use LaTeX-style notation for mathematical expressions. The shared configuration
uses Arithmatex to preserve the notation and [MathJax](https://www.mathjax.org/)
to render it in the browser. The pinned MathJax renderer loads from jsDelivr only
on pages containing equations, so those pages need network access for rendering.

## Inline equations

Place a short expression between single dollar signs to keep it within a sentence.

```markdown
For $n$ observations, the sample mean is $\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$.
```

For $n$ observations, the sample mean is $\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$.

## Display equations

Use double dollar signs on separate lines for an equation that deserves its own block.

```latex
$$
s^2 = \frac{1}{n-1} \sum_{i=1}^{n} (x_i - \bar{x})^2
$$
```

$$
s^2 = \frac{1}{n-1} \sum_{i=1}^{n} (x_i - \bar{x})^2
$$

Here $s^2$ is the sample variance and $n > 1$ is the number of observations.

## Multiple lines

```latex
$$
\begin{aligned}
T_{\mathrm{total}} &= T_{\mathrm{setup}} + T_{\mathrm{run}} \\
\mathrm{throughput} &= \frac{N}{T_{\mathrm{run}}}
\end{aligned}
$$
```

$$
\begin{aligned}
T_{\mathrm{total}} &= T_{\mathrm{setup}} + T_{\mathrm{run}} \\
\mathrm{throughput} &= \frac{N}{T_{\mathrm{run}}}
\end{aligned}
$$

Explain symbols in prose: $N$ is the number of completed operations, and
$T_{\mathrm{run}}$ is the measured execution time.
