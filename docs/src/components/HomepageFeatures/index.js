import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Easy to Use',
    Svg: null,
    description: (
      <>
        CodeQL Wrapper is designed from the ground up to be easily installed and
        configured. Get powerful code security analysis running in minutes, not hours.
      </>
    ),
  },
  {
    title: 'Works on any CI',
    Svg: null,
    description: (
      <>
        Seamlessly integrate CodeQL analysis into your CI/CD pipeline.
        Our wrapper simplifies setup and configuration, letting you focus on
        code security while we handle the complexity.
      </>
    ),
  },
  {
    title: 'Open Source',
    Svg: null,
    description: (
      <>
        Fully open source and community-driven. Extend or customize the wrapper
        to fit your specific security requirements and contribute back to the ecosystem.
      </>
    ),
  },
];

function Feature({ Svg, title, description }) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding--md">
        {Svg && <Svg className={styles.featureSvg} role="img" />}
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
