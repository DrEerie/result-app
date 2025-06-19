import React from 'react';

const Result = ({ results }) => {
    return (
        <div className="result-container">
            <h2>Results</h2>
            {results.length > 0 ? (
                <ul>
                    {results.map((result, index) => (
                        <li key={index}>
                            {result.name}: {result.score}
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No results available.</p>
            )}
        </div>
    );
};

export default Result;